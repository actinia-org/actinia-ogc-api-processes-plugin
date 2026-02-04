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
from flask import has_request_context, request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.resources.config import ACTINIA


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
        {"param": key, "value": value} for key, value in inputs.items()
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


def post_process_execution(
    process_id: str | None = None,
    postbody: str | None = None,
):
    """Start job for given process_id."""
    # Authentication for actinia
    auth = request.authorization
    kwargs = dict()
    kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    project_name = ACTINIA.default_project
    resp = requests.get(
        f"{ACTINIA.processing_base_url}/actinia_modules/{process_id}",
        **kwargs,
    )
    # TODO: Do we stick to the convention introduced in
    # https://github.com/actinia-org/actinia-module-plugin/pull/64
    # that the project name must be set in the template?
    # Or do we add it as a parameter in the process description?
    # If in template, a string would make more sense instead of listing
    # all projects which with the module was tested.
    if resp.status_code == 200 and len(resp.json().get("projects")) > 1:
        project_name = resp.json().get("projects")[0]

    pc = _transform_to_actinia_process_chain(process_id, postbody)
    kwargs["json"] = pc

    # Start process via actinia-module-plugin
    url_process_execution = (
        f"{ACTINIA.processing_base_url}/projects/{project_name}/"
        "processing_export"
    )

    return requests.post(
        url_process_execution,
        **kwargs,
    )
