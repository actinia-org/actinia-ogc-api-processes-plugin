#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Core helper to fetch job status from actinia processing API.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

import requests
from flask import request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.core.actinia_common import (
    parse_actinia_job,
)
from actinia_ogc_api_processes_plugin.resources.config import ACTINIA


def get_actinia_job(job_id):
    """Retrieve job status from actinia."""
    auth = request.authorization
    kwargs = dict()
    if auth:
        kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    url = (
        f"{ACTINIA.processing_base_url}/resources/{auth.username}/"
        f"resource_id-{job_id}"
    )
    return requests.get(url, **kwargs)


def cancel_actinia_job(job_id):
    """Send a DELETE request to actinia to cancel the given job.

    Returns the raw `requests.Response` object.
    """
    auth = request.authorization
    kwargs = dict()
    if auth:
        kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    url = (
        f"{ACTINIA.processing_base_url}/resources/{auth.username}/"
        f"resource_id-{job_id}"
    )
    return requests.delete(url, **kwargs)


def add_actinia_logs(status_info, data):
    """Add a link to the actinia job log to the given status_info dict."""
    actinia_log_url = data["urls"]["status"].replace(
        r"https?://[^/]+/api/v\d+",
        ACTINIA.user_actinia_base_url,
    )
    if "links" not in status_info:
        status_info["links"] = list()
    # rel type from IANA link relations
    status_info["links"].append(
        {
            "href": actinia_log_url,
            "title": "Full actinia job log",
            "rel": "convertedfrom",
        },
    )


def get_job_status_info(job_id):
    """Return a tuple (status_code, status_info_dict_or_None, response).

    Maps the actinia job response into the OGC `statusInfo` structure when
    possible. `response` is the original requests.Response for logging.
    """
    resp = get_actinia_job(job_id)

    status_code = resp.status_code

    if status_code == 200:
        data = resp.json()
        status_info = parse_actinia_job(job_id, data)
        add_actinia_logs(status_info, data)
        return 200, status_info, resp

    # Actinia returns HTTP 400 both for 'no such job' and for
    # resources that include an error state. Distinguish by inspecting the
    # JSON payload: if it looks like a job/resource object (contains
    # identifiers or job fields) treat it as a valid resource and map it to
    # a 200 + statusInfo. Otherwise return 404.
    if status_code == 400:
        try:
            data = resp.json()
        except (ValueError, TypeError):
            return 404, None, resp

        indicative_keys = {
            "accept_timestamp",
            "message",
            "status",
            "resource_id",
            "timestamp",
        }

        if isinstance(data, dict) and indicative_keys.issubset(data.keys()):
            status_info = parse_actinia_job(job_id, data)
            add_actinia_logs(status_info, data)
            return 200, status_info, resp

        return 404, None, resp

    # Any other status codes return as-is
    return status_code, None, resp
