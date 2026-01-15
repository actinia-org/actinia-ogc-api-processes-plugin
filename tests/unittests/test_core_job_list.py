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
    def __init__(self, json_data):
        self._json = json_data

    def json(self):
        return self._json


@pytest.mark.unittest
def test_parse_actinia_jobs_filter_by_processID():
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
