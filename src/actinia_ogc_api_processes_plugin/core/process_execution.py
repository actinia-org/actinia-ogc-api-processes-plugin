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


def post_process_execution(
    process_id: str | None = None,
    postbody: str | None = None,
):
    """Start job for given process_id."""
    # Authentication for actinia
    auth = request.authorization
    kwargs = dict()
    kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)
    kwargs["json"] = postbody

    # Start process via actinia-module-plugin
    url_process_execution = (
        f"{ACTINIA.processing_base_url}/actinia_modules/{process_id}/process"
    )

    return requests.post(
        url_process_execution,
        **kwargs,
    )
