#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Unit tests for core.job_list parse_actinia_jobs filtering.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import pytest

from actinia_ogc_api_processes_plugin.core import job_list as core


class MockResp:
    """Mock requests.Response with json() method."""

    def __init__(self, json_data) -> None:
        """Initialise with json_data."""
        self._json = json_data

    def json(self):
        """Return the json data."""
        return self._json


@pytest.mark.unittest
def test_parse_actinia_jobs_filter_by_processid():
    """parse_actinia_jobs should filter jobs by processID or jobID."""
    # two sample resources: one with resource_id prefix, one with direct id
    items = [
        {
            "resource_id": "resource_id-aaa",
            "status": "running",
            "links": [{"href": "http://example.com/x", "rel": "self"}],
        },
        {
            "resource_id": "resource_id-bbb",
            "status": "finished",
            "links": [{"href": "http://example.com/y", "rel": "self"}],
        },
    ]

    resp = MockResp({"resource_list": items})

    # no filter -> both jobs returned
    out = core.parse_actinia_jobs(resp)
    assert "jobs" in out
    assert len(out["jobs"]) == 2

    # filter by full processID (resource_id value)
    out2 = core.parse_actinia_jobs(resp, process_ids=["resource_id-aaa"])
    assert len(out2["jobs"]) == 1
    assert out2["jobs"][0]["processID"] == "resource_id-aaa"

    # filter by short jobID (removeprefix)
    out3 = core.parse_actinia_jobs(resp, process_ids=["bbb"])
    assert len(out3["jobs"]) == 1
    assert out3["jobs"][0]["jobID"] == "bbb"


@pytest.mark.unittest
def test_parse_actinia_jobs_filter_by_status():
    """parse_actinia_jobs should filter jobs by status values."""
    items = [
        {
            "resource_id": "resource_id-aaa",
            "status": "running",
            "links": [{"href": "http://example.com/x", "rel": "self"}],
        },
        {
            "resource_id": "resource_id-bbb",
            "status": "finished",
            "links": [{"href": "http://example.com/y", "rel": "self"}],
        },
    ]

    resp = MockResp({"resource_list": items})

    # no filter -> both jobs returned
    out = core.parse_actinia_jobs(resp)
    assert len(out["jobs"]) == 2

    # filter by OGC status 'running'
    out_run = core.parse_actinia_jobs(resp, status=["running"])
    assert len(out_run["jobs"]) == 1
    assert out_run["jobs"][0]["status"] == "running"

    # filter by OGC status 'successful' (maps from actinia 'finished')
    out_succ = core.parse_actinia_jobs(resp, status=["successful"])
    assert len(out_succ["jobs"]) == 1
    assert out_succ["jobs"][0]["status"] == "successful"

    # filter by multiple statuses
    out_both = core.parse_actinia_jobs(resp, status=["running", "successful"])
    assert len(out_both["jobs"]) == 2


@pytest.mark.unittest
def test_parse_actinia_jobs_filter_by_datetime():
    """parse_actinia_jobs should filter jobs by created datetime."""
    # two sample resources with accept_timestamp -> created
    # 2021-01-01T00:00:00Z and 2021-01-02T00:00:00Z
    items = [
        {
            "resource_id": "resource_id-aaa",
            "status": "running",
            "accept_timestamp": "1609459200",
            "links": [{"href": "http://example.com/x", "rel": "self"}],
        },
        {
            "resource_id": "resource_id-bbb",
            "status": "finished",
            "accept_timestamp": "1609545600",
            "links": [{"href": "http://example.com/y", "rel": "self"}],
        },
    ]

    resp = MockResp({"resource_list": items})

    # no filter -> both jobs returned
    out = core.parse_actinia_jobs(resp)
    assert len(out["jobs"]) == 2

    # single exact datetime -> only first job
    out_single = core.parse_actinia_jobs(
        resp,
        datetime_param="2021-01-01T00:00:00+00:00",
    )
    assert len(out_single["jobs"]) == 1
    assert out_single["jobs"][0]["processID"] == "resource_id-aaa"

    # closed interval covering both -> both jobs
    out_closed = core.parse_actinia_jobs(
        resp,
        datetime_param="2021-01-01T00:00:00+00:00/2021-01-02T00:00:00+00:00",
    )
    assert len(out_closed["jobs"]) == 2

    # open start: '/../2021-01-01T12:00:00+00:00'
    # -> only first (00:00) <= 12:00
    out_open_start = core.parse_actinia_jobs(
        resp,
        datetime_param="/2021-01-01T12:00:00+00:00",
    )
    assert len(out_open_start["jobs"]) == 1

    # open end: '2021-01-02T00:00:00+00:00/..' -> only second (>=)
    out_open_end = core.parse_actinia_jobs(
        resp,
        datetime_param="2021-01-02T00:00:00+00:00/..",
    )
    assert len(out_open_end["jobs"]) == 1
