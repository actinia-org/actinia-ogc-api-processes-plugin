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
    safe_parse_actinia_job,
)
from actinia_ogc_api_processes_plugin.resources.config import ACTINIA
from actinia_ogc_api_processes_plugin.resources.logging import log


def get_actinia_jobs(
    actinia_type: str | None = None,
    limit: int | None = None,
):
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
    if limit is not None:
        if not params:
            params = {}
        params["num"] = str(limit)
    try:
        if params:
            return requests.get(url, params=params, **kwargs)
        return requests.get(url, **kwargs)
    except Exception as e:  # let callers translate connection errors
        log.debug(f"Error while requesting actinia jobs: {e}")
        raise


def _generate_new_joblinks(job_id: str) -> list[dict]:
    """Make sure job_id is in the link."""
    base = request.base_url.rstrip("/") if has_request_context() else "/jobs"
    job_href = f"{base}/{job_id}"
    return [{"href": job_href, "rel": "status"}]


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
    job_types: list | None,
    process_ids: list | None,
    status: list | None,
) -> bool:
    """Return True when `status_info` passes provided filters."""
    # apply optional filtering by type (query parameter)
    # Requirement 66: If the parameter is provided and its value is process
    # then only jobs created by an OGC processes API SHALL be included in the
    # response.
    # Additionally, support filtering by other job types as well.
    if job_types and status_info.get("type") not in job_types:
        return False

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


def _matches_duration_filters(
    status_info,
    min_duration: int | None = None,
    max_duration: int | None = None,
) -> bool:
    """Return True when `status_info` passes provided duration filters.

    When status is "running": Duration is now - created. When status is
    "successful", "failed", "dismissed": Duration is finished - created.
    If no min/max provided returns True. If duration cannot be computed
    while filtering is requested, return False.
    """
    if min_duration is None and max_duration is None:
        return True

    def _parse(dt_str):
        if not dt_str:
            return None
        v = dt_str.replace("Z", "+00:00") if dt_str.endswith("Z") else dt_str
        try:
            dt = datetime.fromisoformat(v)
        except (TypeError, ValueError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    s = (status_info.get("status") or "").lower()
    started = _parse(status_info.get("started"))
    finished = _parse(status_info.get("finished"))

    if s == "running":
        if not started:
            return False
        dur = (datetime.now(timezone.utc) - started).total_seconds()
    elif s in {"successful", "failed", "dismissed"}:
        if not started or not finished:
            return False
        dur = (finished - started).total_seconds()
    else:
        # duration undefined for other states -> exclude when filtering
        return False

    if min_duration is not None and dur < float(min_duration):
        return False
    return not (max_duration is not None and dur > float(max_duration))


def parse_actinia_jobs(
    resp,
    job_types: list | None = None,
    process_ids: list | None = None,
    status: list | None = None,
    datetime_param: str | None = None,
    min_duration: int | None = None,
    max_duration: int | None = None,
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
        job_id, status_info = safe_parse_actinia_job(item)
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
            job_types,
            process_ids,
            status,
        ):
            continue

        if not _matches_datetime_filters(
            status_info,
            datetime_interval,
        ):
            continue

        if not _matches_duration_filters(
            status_info,
            min_duration,
            max_duration,
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
