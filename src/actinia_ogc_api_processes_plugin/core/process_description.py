#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Example core functionality
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import requests
from flask import request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.resources.config import ACTINIA


def get_module_description(process_id):
    """Get modules description for given process_id."""
    # Authentication for actinia
    auth = request.authorization
    kwargs = dict()
    kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    # Get module description
    url_module_description = (
        f"{ACTINIA.processing_base_url}/modules/{process_id}"
    )
    # NOTE:
    # The standard does not mandate the use of a specific process description.
    # However following recommendation is given:
    # Implementations SHOULD consider supporting the OGC process description:
    # https://docs.ogc.org/is/18-062r2/18-062r2.html#ogc_process_description

    return requests.get(
        url_module_description,
        **kwargs,
    )


def update_resp(resp_json: dict) -> dict:
    """Append GRASS GIS project to input description and jobControlOptions."""
    project_input = {
        "description": "Name of GRASS GIS project to use",
        "name": "project",
        "optional": False,
        "schema": {"type": "string"},
        "default": ACTINIA.default_project,
    }
    resp_json["parameters"].append(project_input)

    # currently only asynchronous processing is supported
    resp_json["jobControlOptions"] = [
        "async-execute",
    ]

    # Convert list of parameters to a dict keyed by parameter name
    params = resp_json.pop("parameters", [])
    inputs = {}
    for p in params:
        name = p.get("name")
        if name is None:
            continue
        # keep parameter fields but remove the redundant 'name' field
        value = {k: v for k, v in p.items() if k != "name"}
        inputs[name] = value
    resp_json["inputs"] = inputs

    # Same for returns/outputs
    returns = resp_json.pop("returns", [])
    outputs = {}
    for r in returns:
        name = r.get("name")
        if name is None:
            continue
        value = {k: v for k, v in r.items() if k != "name"}
        outputs[name] = value
    resp_json["outputs"] = outputs

    return resp_json
