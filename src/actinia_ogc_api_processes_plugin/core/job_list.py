#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Core helper to fetch job list from actinia processing API.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import request
import requests
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.resources.config import ACTINIA
from actinia_ogc_api_processes_plugin.resources.logging import log
from actinia_ogc_api_processes_plugin.core.job_status_info import (
    parse_actinia_job,
)


def get_actinia_jobs():
    """Retrieve job list from actinia for current user.

    Returns the raw requests.Response from actinia so callers can decide how
    to handle different status codes.
    """
    auth = request.authorization
    kwargs = dict()
    if auth:
        kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    url = f"{ACTINIA.processing_base_url}/resources/{auth.username}"
    try:
        return requests.get(url, **kwargs)
    except Exception as e:  # let callers translate connection errors
        log.debug(f"Error while requesting actinia jobs: {e}")
        raise


def parse_actinia_jobs(resp):
    """Map actinia response into a `jobs` list structure.

    Reuses `parse_actinia_job`.
    """
    try:
        data = resp.json()
    except (ValueError, TypeError):
        data = {}

    if isinstance(data, dict) and "resource_list" in data:
        items = data["resource_list"] or []
    else:
        items = []

    jobs = []

    for item in items:
        if not isinstance(item, dict):
            continue
        job_id = item.get("resource_id").strip("resource_id-")
        if not job_id:
            continue

        try:
            status_info = parse_actinia_job(job_id, item)
        except Exception:
            status_info = {
                "jobID": job_id,
                "type": "process",
                "processID": item.get("resource_id"),
                "status": item.get("status"),
                "links": [],
            }

        # Ensure links point to the single job resource (/jobs/{job_id})
        if job_id not in status_info.get("links"):
            job_href = f"{request.url.rstrip('/')}/{job_id}"
            new_links = [{"href": job_href, "rel": "status"}]
        status_info["links"] = new_links

        jobs.append(status_info)

    resp_format = {
        "jobs": jobs,
        "links": [
            {
                "href": f"{request.url}?f=json",
                "rel": "self",
                "type": "application/json",
            }
        ],
    }
    return resp_format
