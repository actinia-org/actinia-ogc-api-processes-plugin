#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Core helper to fetch job list from actinia processing API.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from datetime import datetime, timezone

import requests
from flask import has_request_context, request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.core.actinia_common import (
    parse_actinia_job,
)
from actinia_ogc_api_processes_plugin.resources.config import ACTINIA
from actinia_ogc_api_processes_plugin.resources.logging import log


def get_actinia_jobs(actinia_type: str | None = None):
    """Retrieve job list from actinia for current user.

    Returns the raw requests.Response from actinia so callers can decide how
    to handle different status codes.
    """
    auth = request.authorization
    kwargs = dict()
    if auth:
        kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    url = f"{ACTINIA.processing_base_url}/resources/{auth.username}"
    params = None
    if actinia_type:
        params = {"type": actinia_type}
    try:
        if params:
            return requests.get(url, params=params, **kwargs)
        return requests.get(url, **kwargs)
    except Exception as e:  # let callers translate connection errors
        log.debug(f"Error while requesting actinia jobs: {e}")
        raise


def _generate_new_joblinks(job_id: str) -> list[dict]:
    """Make sure job_id is in the link."""
    base = request.url.rstrip("/") if has_request_context() else "/jobs"
    job_href = f"{base}/{job_id}"
    return [{"href": job_href, "rel": "status"}]


def _safe_parse_item(item):
    """Return (job_id, status_info) or (None, None) for invalid items."""
    if not isinstance(item, dict):
        return None, None
    job_id = item.get("resource_id").removeprefix("resource_id-")
    if not job_id:
        return None, None
    try:
        status_info = parse_actinia_job(job_id, item)
    except (TypeError, ValueError):
        status_info = {
            "jobID": job_id,
            "type": "process",
            "processID": item.get("resource_id"),
            "status": item.get("status"),
            "links": [],
        }
    return job_id, status_info


def _get_datetime_interval(datetime_param):
    """Parse datetime query parameter into (start, end) datetime tuple.

    value can be either a single date-time or an interval 'start/end'.
    """
    if not datetime_param:
        return None

    try:
        if "/" in datetime_param:
            left, right = datetime_param.split("/", 1)
            # interpret empty string or '..' as open bound
            if left in {"", ".."}:
                start = None
            else:
                s = left.replace("Z", "+00:00") if left.endswith("Z") else left
                start = datetime.fromisoformat(s)
            if right in {"", ".."}:
                end = None
            else:
                r = (
                    right.replace("Z", "+00:00")
                    if right.endswith("Z")
                    else right
                )
                end = datetime.fromisoformat(r)
        else:
            # single datetime -> treat as instant interval
            v = (
                datetime_param.replace("Z", "+00:00")
                if datetime_param.endswith("Z")
                else datetime_param
            )
            instant = datetime.fromisoformat(v)
            start = instant
            end = instant
        datetime_interval = (start, end)
    except (TypeError, ValueError):
        # invalid datetime format -> no matches
        datetime_interval = (None, None)
    return datetime_interval


def _matches_filters(
    status_info,
    process_ids: list | None,
    status: list | None,
) -> bool:
    """Return True when `status_info` passes provided filters."""
    # apply optional filtering by processIDs (query parameter)
    if process_ids:
        pid_val = status_info.get("processID")
        jid_val = status_info.get("jobID")
        matched = any(pid in {pid_val, jid_val} for pid in process_ids)
        if not matched:
            return False
    # apply optional filtering by status (query parameter)
    # single status is filtered by actinia request directly
    if status:
        s_val = status_info.get("status")
        allowed = {st.lower() for st in status}
        if not s_val or s_val.lower() not in allowed:
            return False
    return True


def _matches_datetime_filters(
    status_info,
    datetime_interval: tuple | None = None,
) -> bool:
    """Return True when `status_info` passes provided filters."""
    # apply optional filtering by datetime (query parameter)
    if datetime_interval:
        # datetime_interval is (start, end) with start/end are datetime or None
        created_val = status_info.get("created")
        if not created_val:
            return False
        try:
            # support 'Z' suffix
            if created_val.endswith("Z"):
                created_dt = datetime.fromisoformat(
                    created_val.replace("Z", "+00:00"),
                )
            else:
                created_dt = datetime.fromisoformat(created_val)
        except (TypeError, ValueError):
            return False

        start, end = datetime_interval
        # convert naive datetimes to timezone-aware UTC if needed
        if start is not None and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end is not None and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        if start and end:
            if not (start <= created_dt <= end):
                return False
        elif start and not end:
            if not (created_dt >= start):
                return False
        elif end and not start and not (created_dt <= end):
            return False
    return True


def parse_actinia_jobs(
    resp,
    process_ids: list | None = None,
    status: list | None = None,
    datetime_param: str | None = None,
):
    """Map actinia response into a `jobs` list structure.

    Reuses `parse_actinia_job`.

    If `process_ids` is provided, only include jobs matching any of the
    provided process identifiers (match against `processID` or `jobID`).
    """
    try:
        items = resp.json()["resource_list"]
    except (ValueError, TypeError):
        items = []

    jobs = []

    for item in items:
        job_id, status_info = _safe_parse_item(item)
        if not job_id:
            continue

        # Ensure links point to the single job resource (/jobs/{job_id})
        if job_id not in status_info.get("links"):
            status_info["links"] = _generate_new_joblinks(job_id)

        # parse optional datetime parameter into (start,end) datetimes
        datetime_interval = _get_datetime_interval(datetime_param)

        # apply optional filtering (query parameters)
        if not _matches_filters(
            status_info,
            process_ids,
            status,
        ):
            continue

        if not _matches_datetime_filters(
            status_info,
            datetime_interval,
        ):
            continue

        jobs.append(status_info)

    self_href = "/jobs?f=json"
    if has_request_context():
        self_href = f"{request.url}?f=json"

    return {
        "jobs": jobs,
        "links": [
            {
                "href": self_href,
                "rel": "self",
                "type": "application/json",
            },
        ],
    }
