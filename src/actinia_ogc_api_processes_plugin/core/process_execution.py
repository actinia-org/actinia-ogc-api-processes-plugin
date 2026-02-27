#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Process Execution core functionality
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika, Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import requests
from flask import has_request_context, jsonify, make_response, request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)
from actinia_ogc_api_processes_plugin.resources.config import ACTINIA

GRASS_MODULE_TYPE = {
    "d": "display",
    "db": "database",
    "g": "general",
    "i": "imagery",
    "m": "miscellaneous",
    "r": "raster",
    "r3": "3Draster",
    "t": "temporal",
    "v": "vector",
}


def generate_new_joblinks(job_id: str) -> list[dict]:
    """Make sure job_id is in the link."""
    base = request.url_root.rstrip("/") if has_request_context() else "/"
    job_href = f"{base}/jobs/{job_id}"
    return [{"href": job_href, "rel": "status"}]


def _transform_to_actinia_process_chain(
    process_id: str,
    execute_request: dict,
) -> dict:
    """Transform execute postbody to actinia process chain format."""
    inputs = execute_request.get("inputs", [])
    pc = {
        "list": [
            {
                "id": f"{process_id}_1",
                "module": process_id,
            },
        ],
        "version": "1",
    }
    if inputs:
        inputs_array = [
            {
                "param": key,
                "value": (
                    ",".join(value) if isinstance(value, list) else str(value)
                ),
            }
            for key, value in inputs.items()
            if key not in {"project", "bounding_box"} and len(key) > 1
        ]
        flags_array = [
            key
            for key, value in inputs.items()
            if key != "project" and len(key) == 1 and value is True
        ]
        pc["list"][0]["flags"] = ",".join(flags_array)
        pc["list"][0]["inputs"] = inputs_array

    return pc


def _add_exporter_to_pc_list(
    process_type: str,
    pc_list: list,
    process: dict,
    input_map: str,
):
    """Add exporter to process chain list."""
    out_maps = [
        param["value"]
        for param in process["inputs"]
        if param["param"] == "output"
    ]
    output_map = out_maps[0] if out_maps else input_map
    output_format = "GTiff"  # or COG ?
    if process_type == "vector":
        output_format = "GPKG"
    exporter = {
        "id": "exporter_1",
        "module": "exporter",
        "outputs": [
            {
                "export": {"format": output_format, "type": process_type},
                "param": "map",
                "value": output_map,
            },
        ],
    }
    pc_list.append(exporter)


def _add_regionsetting_to_pc_list(
    process_type: str,
    pc_list: list,
    input_map: str,
):
    """Add region setting to process chain list."""
    set_region = {
        "id": "g_region_1",
        "module": "g.region",
        "inputs": [
            {
                "param": process_type,
                "value": input_map,
            },
        ],
        "flags": "g",
    }
    if process_type == "vector":
        set_region["inputs"].append({"param": "cols", "value": "1"})
    pc_list.insert(0, set_region)


def _add_regionsetting_via_bbox_to_pc_list(
    pc_list: list,
    bounding_box: str,
):
    """Add region setting via bbox to process chain list."""
    set_region = {
        "id": "g_region_1",
        "module": "g.region",
        "inputs": [
            {"param": "w", "value": str(bounding_box[0])},
            {"param": "s", "value": str(bounding_box[1])},
            {"param": "e", "value": str(bounding_box[2])},
            {"param": "n", "value": str(bounding_box[3])},
        ],
        "flags": "g",
    }
    pc_list.insert(0, set_region)


def _add_vclip_to_pc_list(pc_list, input_map):
    """Add clipping of vector input to process chain list."""
    input_map_clipped = f"{input_map}_region_clip"
    v_clip = {
        "id": "v_clip_1",
        "module": "v.clip",
        "flags": "r",
        "inputs": [
            {
                "param": "input",
                "value": input_map,
            },
            {
                "param": "output",
                "value": input_map_clipped,
            },
        ],
    }
    # Overwrite input with clipped result.
    # For now ok, if in future persistent calculation added,
    # adjust cause overwrite probably not wanted.
    g_rename_v_clip = {
        "id": "g_rename_v_clip_1",
        "module": "g.rename",
        "inputs": [
            {
                "param": "vector",
                "value": f"{input_map_clipped},{input_map}",
            },
        ],
    }
    pc_list.insert(1, v_clip)
    pc_list.insert(2, g_rename_v_clip)


# ruff: noqa: PLR0912, PLR0914,
def _invalid_inputs(module_info: dict, inputs: dict):
    """Check if given inputs are valid."""
    """
    Validate provided `inputs` against `module_info` parameters.

    Returns a list of input names that are invalid either because they are
    unknown for the module or because their value does not match the
    declared schema `type`.
    """
    params = module_info.get("parameters", [])
    params += module_info.get("returns", [])
    params.append({"name": "bounding_box", "schema": {"type": "bbox"}})
    params.append({"name": "project", "schema": {"type": "string"}})
    param_map = {
        p.get("name"): p
        for p in params
        if isinstance(p, dict) and p.get("name")
    }

    invalid = []
    msg = ""
    msg_append = ""
    if not inputs:
        return invalid, msg

    for key, val in inputs.items():
        if key not in param_map:
            invalid.append(key)
            continue

        schema = (
            param_map[key].get("schema", {})
            if isinstance(param_map[key], dict)
            else {}
        )
        expected = schema.get("type")

        # if no explicit type in schema, accept the input
        if not expected:
            continue

        if expected == "string":
            if not isinstance(val, str):
                invalid.append(key)
        elif expected == "boolean":
            if not isinstance(val, bool):
                invalid.append(key)
        elif expected == "integer":
            if not (isinstance(val, int) and not isinstance(val, bool)):
                invalid.append(key)
        elif expected == "number":
            if not isinstance(val, (int, float)) and not isinstance(val, bool):
                invalid.append(key)
        elif expected == "array":
            if not isinstance(val, list):
                invalid.append(key)
        elif expected == "bbox":
            # ruff: noqa: PLR0916
            if (
                not isinstance(val, dict)
                or "bbox" not in val
                or not isinstance(val["bbox"], list)
                or (len(val["bbox"]) != 4 and len(val["bbox"]) != 6)
                or not all(
                    isinstance(coord, (int, float)) for coord in val["bbox"]
                )
            ):
                invalid.append(key)
                msg_append += (
                    "Check if 'bounding_box' is dict with key 'bbox'."
                    "'bbox' should be a list of 4 or 6 numbers."
                )
        else:
            # Unknown/unsupported schema type: be permissive and accept
            continue

        if key in invalid:
            msg += (
                f"Input parameter '{key}' should be type {expected},"
                f" but got {type(val).__name__}. {msg_append}"
            )

    return invalid, msg


def post_process_execution(
    process_id: str | None = None,
    postbody: str | None = None,
):
    """Start job for given process_id."""
    # Authentication for actinia
    auth = request.authorization
    kwargs = dict()
    kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    # Check if process exists in actinia
    resp = requests.get(
        f"{ACTINIA.processing_base_url}/modules/{process_id}",
        **kwargs,
    )
    if resp.status_code != 200:
        return resp

    invalid_inputs, detail_msg = _invalid_inputs(
        resp.json(),
        postbody.get("inputs", {}),
    )
    if invalid_inputs:
        invalid_inp_str = ", ".join(str(x) for x in invalid_inputs)
        msg = f"Invalid input <{invalid_inp_str}> for process <{process_id}>."
        res = jsonify(
            SimpleStatusCodeResponseModel(
                status=400,
                message=(msg + " " + detail_msg),
            ),
        )
        return make_response(res, 400)

    project_name = ACTINIA.default_project
    if postbody.get("inputs") and postbody.get("inputs").get("project"):
        project_name = postbody.get("inputs").get("project")

    pc = _transform_to_actinia_process_chain(process_id, postbody)

    # adjust pc if process is grass module
    module_info = resp.json()
    if "grass-module" in module_info["categories"]:
        # get GRASS processing type
        process_type = GRASS_MODULE_TYPE[process_id.split(".", 1)[0]]
        # check if module has input/map parameter
        has_input = any(
            param.get("name") in {"input", "map"}
            for param in module_info.get("parameters", [])
        )
        if not has_input or process_type not in {"raster", "vector"}:
            msg = f"Process execution of <{process_id}> not supported."
            res = jsonify(
                SimpleStatusCodeResponseModel(
                    status=400,
                    message=msg,
                ),
            )
            return make_response(res, 400)

        # adjust PC list
        pc_list = pc["list"]
        process = pc_list[0]
        # add region setting to pc
        input_map = next(
            param["value"]
            for param in process["inputs"]
            if param["param"] in {"input", "map"}
        )
        if postbody.get("inputs").get("bounding_box"):
            # adjust PC if bounding box given
            bounding_box = (
                postbody.get("inputs").get("bounding_box").get("bbox")
            )
            _add_regionsetting_via_bbox_to_pc_list(pc_list, bounding_box)
            if process_type == "vector":
                _add_vclip_to_pc_list(pc_list, input_map)
        else:
            _add_regionsetting_to_pc_list(process_type, pc_list, input_map)
        # add exporter
        _add_exporter_to_pc_list(process_type, pc_list, process, input_map)
    elif postbody.get("inputs").get("bounding_box"):
        # adjust PC if bounding box given
        bounding_box = postbody.get("inputs").get("bounding_box").get("bbox")
        # adjust PC list
        pc_list = pc["list"]
        # Currently always region set via bounding box (if given).
        # If region is also set within actinia module, the region setting
        # via bounding box will be "overwritten".
        # Todo: check if actinia module has already region set.
        # Note: importer hast 'extents' as parameter
        _add_regionsetting_via_bbox_to_pc_list(
            pc_list,
            bounding_box,
        )

    # Start process via actinia-module-plugin
    kwargs["json"] = pc
    url_process_execution = (
        f"{ACTINIA.processing_base_url}/projects/{project_name}/"
        "processing_export"
    )

    return requests.post(
        url_process_execution,
        **kwargs,
    )
