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
            if key != "project" and len(key) > 1
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
    }
    if process_type == "vector":
        set_region["inputs"].append({"param": "cols", "value": "1"})
    pc_list.insert(0, set_region)


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
    params.append({"name": "project", "schema": {"type": "string"}})
    param_map = {
        p.get("name"): p
        for p in params
        if isinstance(p, dict) and p.get("name")
    }

    invalid = []
    msg = ""
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
        else:
            # Unknown/unsupported schema type: be permissive and accept
            continue

        if key in invalid:
            msg += (
                f"Input parameter '{key}' should be {expected},"
                f" but got {type(val).__name__}."
            )

    return invalid, msg


def _missing_inputs(module_info: dict, inputs: dict):
    """Check if required inputs are missing."""
    params = module_info.get("parameters", [])
    params += module_info.get("returns", [])
    required_params = {p.get("name") for p in params if not p.get("optional")}
    return [param for param in required_params if param not in inputs]


def is_valid_postbody(postbody: dict) -> bool:
    """Check if postbody is valid."""
    allowed_keys = {"inputs", "outputs", "response", "subscriber"}
    wrong_key = any(key not in allowed_keys for key, value in postbody.items())
    return not wrong_key


def post_process_execution(
    process_id: str | None = None,
    postbody: dict | None = None,
):
    """Start job for given process_id."""
    if not is_valid_postbody(postbody):
        res = jsonify(
            {
                "type": "InvalidRequestBody",
                "title": "Invalid request body",
                "status": 400,
                "detail": "Request body contains invalid keys.",
            },
        )
        return make_response(res, 400)

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
            {
                "type": "InvalidInput",
                "title": "Invalid input",
                "status": 400,
                "detail": (msg + " " + detail_msg),
            },
        )
        return make_response(res, 400)

    missing_inputs = _missing_inputs(
        resp.json(),
        postbody.get("inputs", {}),
    )
    if missing_inputs:
        missing_inputs_str = ", ".join(str(x) for x in missing_inputs)
        msg = (
            f"Missing required input parameter <{missing_inputs_str}> for "
            f"process <{process_id}>."
        )
        res = jsonify(
            {
                "type": "InvalidInput",
                "title": "Missing required input",
                "status": 400,
                "detail": msg,
            },
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
        # check if module hast input/map parameter
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
        _add_regionsetting_to_pc_list(process_type, pc_list, input_map)
        # add exporter
        _add_exporter_to_pc_list(process_type, pc_list, process, input_map)

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
