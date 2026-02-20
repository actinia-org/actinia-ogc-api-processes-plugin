#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Process Execution core functionality
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika, Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import json

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
    inputs_array = [
        {"param": key, "value": value}
        for key, value in inputs.items()
        if key != "project"
    ]

    return {
        "list": [
            {
                "id": f"{process_id}_1",
                "module": process_id,
                "inputs": inputs_array,
            },
        ],
        "version": "1",
    }


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

    project_name = ACTINIA.default_project
    if postbody.get("inputs").get("project"):
        project_name = postbody.get("inputs").get("project")

    pc = _transform_to_actinia_process_chain(process_id, postbody)

    # adjust pc if process is grass module
    module_info = json.loads(resp.text)
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
                    status=405,
                    message=msg,
                ),
            )
            return make_response(res, 405)

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
