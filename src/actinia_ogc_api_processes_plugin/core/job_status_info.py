#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Core helper to fetch job status from actinia processing API.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from datetime import datetime, timedelta, timezone

import requests
from flask import request
from requests.auth import HTTPBasicAuth

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


def map_status(raw: object) -> str:
    """Map actinia status values to OGC statusInfo values.

    Mapping:
      - accepted   -> accepted
      - running    -> running
      - finished   -> successful
      - error      -> failed
      - terminated -> dismissed

    Default is 'accepted' when input is falsy or unknown.
    """
    if not raw:
        return "accepted"
    s = str(raw).strip().lower()
    mapping = {
        "accepted": "accepted",
        "running": "running",
        "finished": "successful",
        "error": "failed",
        "terminated": "dismissed",
    }
    return mapping.get(s, "accepted")


def calculate_progress(data: dict):
    """Return integer progress 0..100 from data or None.

    Supports nested object `progress: { num_of_steps, step }`.
    Returns None on invalid input.
    """
    status = data.get("status")
    progress = data.get("progress")
    if not isinstance(progress, dict):
        return None
    if status == "finished":
        return 100

    try:
        raw_num = progress.get("num_of_steps")
        raw_cur = progress.get("step")
        num = int(raw_num) if isinstance(raw_num, int) else int(float(raw_num))
        cur = int(raw_cur) if isinstance(raw_cur, int) else int(float(raw_cur))
    except (TypeError, ValueError):
        return None

    if num <= 0:
        return None
    # calculate percentage with total steps + 1 to avoid 100% before finished
    prog = round((cur / (num + 1)) * 100)
    return max(0, min(100, prog))


def calculate_finished(data: dict):
    """Return finished time as ISO string or None.

    Calculate `finished` from accept_timestamp + time_delta (seconds)
    """
    status = data.get("status")
    if status != "finished":
        return None
    start = data.get("accept_timestamp")

    try:
        start_dt = datetime.fromtimestamp(float(start), tz=timezone.utc)
        td = float(data.get("time_delta"))
    except (TypeError, ValueError):
        return None

    finished_dt = start_dt + timedelta(seconds=td)
    # format without microseconds
    return finished_dt.replace(microsecond=0).isoformat()


def parse_actinia_job(job_id, resp):
    """Parse actinia job response into status_info dict."""
    try:
        data = resp.json()
    except (ValueError, TypeError):
        data = {}

    status_info = {}
    status_info["jobID"] = job_id
    status_info["status"] = map_status(data.get("status"))
    status_info["type"] = data.get("type", "process")
    status_info["message"] = data.get("message")
    status_info["processID"] = data.get("resource_id")

    # Servers SHOULD set the value of the created field when a job has been
    # accepted and queued for execution.
    try:
        created = datetime.fromtimestamp(
            float(data.get("accept_timestamp")),
            tz=timezone.utc,
        )
        status_info["created"] = created.replace(microsecond=0).isoformat()
    except (TypeError, ValueError):
        pass

    # Whenever the status field of the job changes, servers SHOULD revise the
    # value of the updated field.
    # -> actinia-core updates this field every time anything was updated.
    try:
        updated = datetime.fromtimestamp(
            float(data.get("timestamp")),
            tz=timezone.utc,
        )
        status_info["updated"] = updated.replace(microsecond=0).isoformat()
    except (TypeError, ValueError):
        pass

    # Servers SHOULD set the value of the started field when a job begins
    # execution and is consuming compute resources.
    # status_info["started"] = # TODO implement in actinia-core

    # Servers SHOULD set the value of the finished field when the execution of
    # a job has completed and the process is no longer consuming compute
    # resources.
    # -> Returns none of job not finished.
    finished_val = calculate_finished(data)
    if finished_val is not None:
        status_info["finished"] = finished_val

    progress_val = calculate_progress(data)
    if progress_val is not None:
        status_info["progress"] = progress_val

    links = data.get("links")
    if not links:
        links = [{"href": request.url, "rel": "self"}]
    status_info["links"] = links

    return status_info


def get_job_status_info(job_id):
    """Return a tuple (status_code, status_info_dict_or_None, response).

    Maps the actinia job response into the OGC `statusInfo` structure when
    possible. `response` is the original requests.Response for logging.
    """
    resp = get_actinia_job(job_id)

    status_code = resp.status_code

    if status_code == 200:
        status_info = parse_actinia_job(job_id, resp)
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
            status_info = parse_actinia_job(job_id, resp)
            return 200, status_info, resp

        return 404, None, resp

    # Any other status codes return as-is
    return status_code, None, resp
