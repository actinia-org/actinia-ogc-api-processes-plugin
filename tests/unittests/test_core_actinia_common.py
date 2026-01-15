#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Unit tests for core.job_status_info helper functions.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import pytest

from actinia_ogc_api_processes_plugin.core import actinia_common as actinia


class MockResp:
    """Lightweight Response-like object for unit tests.

    Provides `status_code`, `text` and a `json()` method returning the
    configured payload.
    """

    def __init__(self, status_code=200, json_data=None, text="") -> None:
        """Initialise."""
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        """Return the configured response json."""
        return self._json


@pytest.mark.unittest
def test_map_status_values():
    """Test mapping of actinia job status to OGC API Processes values."""
    assert actinia.map_status("accepted") == "accepted"
    assert actinia.map_status("running") == "running"
    assert actinia.map_status("finished") == "successful"
    assert actinia.map_status("error") == "failed"
    assert actinia.map_status("terminated") == "dismissed"
    assert actinia.map_status(None) == "accepted"
    assert actinia.map_status("unknown") == "accepted"


@pytest.mark.unittest
def test_calculate_progress_valid_and_invalid():
    """Test calculation of progress percentage from actinia progress info."""
    # valid integer steps
    data = {"progress": {"num_of_steps": 4, "step": 2}}
    # calculation uses num+1 denominator -> 2/(4+1) = 0.4 -> 40
    assert actinia.calculate_progress(data) == 40

    # step > num -> clamp to 100
    data = {"progress": {"num_of_steps": 3, "step": 5}}
    assert actinia.calculate_progress(data) == 100

    # string floats
    data = {"progress": {"num_of_steps": "4", "step": "1"}}
    # 1/(4+1) = 0.2 -> 20
    assert actinia.calculate_progress(data) == 20

    # not a dict -> None
    assert actinia.calculate_progress({"progress": 50}) is None
    # invalid values -> None
    data = {"progress": {"num_of_steps": 0, "step": 0}}
    assert actinia.calculate_progress(data) is None


@pytest.mark.unittest
def test_calculate_finished():
    """Test calculation of finished timestamp."""
    # 2021-01-01T00:00:00Z + 3600s -> 2021-01-01T01:00:00+00:00
    data = {
        "accept_timestamp": 1609459200,
        "time_delta": 3600,
        "status": "finished",
    }
    assert actinia.calculate_finished(data) == "2021-01-01T01:00:00+00:00"


@pytest.mark.unittest
def test_calculate_finished_but_still_running():
    """Test that finished is None when job not finished."""
    # 2021-01-01T00:00:00Z + 3600s -> 2021-01-01T01:00:00+00:00
    data = {
        "accept_timestamp": 1609459200,
        "time_delta": 3600,
        "status": "running",
    }
    assert actinia.calculate_finished(data) is None


@pytest.mark.unittest
def test_parse_actinia_job_with_valid_data():
    """Test parsing of actinia job response into status_info dict."""
    sample = {
        "status": "running",
        "resource_id": "resource_id-96ed4cb9-1290-4409-b034-c162759c10a1",
        "accept_timestamp": 1767697334.010796,
        "timestamp": 1767697369.8468018,
        "time_delta": 35.83603835105896,
        "progress": {"num_of_steps": 4, "step": 2},
        "type": "process",
        "message": "ok",
        "links": [{"href": "http://example.com/out", "rel": "alternate"}],
    }

    data = MockResp(200, json_data=sample, text="ok").json()
    info = actinia.parse_actinia_job(
        "96ed4cb9-1290-4409-b034-c162759c10a1",
        data,
    )
    assert info["jobID"] == "96ed4cb9-1290-4409-b034-c162759c10a1"
    assert info["status"] == "running"
    expected_proc = "resource_id-96ed4cb9-1290-4409-b034-c162759c10a1"
    assert info["processID"] == expected_proc
    assert info["created"] == "2026-01-06T11:02:14+00:00"
    assert info["updated"] == "2026-01-06T11:02:49+00:00"
    assert "finished" not in info
    # progress -> 2/(4+1) = 0.4 -> 40
    assert info["progress"] == 40
    assert isinstance(info["links"], list)
    assert info["links"][0]["href"] == "http://example.com/out"


@pytest.mark.unittest
def test_parse_actinia_job_finished_status():
    """Test parsing of actinia job response with finished status."""
    sample = {
        "status": "finished",
        "resource_id": "resource_id-96ed4cb9-1290-4409-b034-c162759c10a1",
        "accept_timestamp": 1767697334.010796,
        "timestamp": 1767697369.8468018,
        "time_delta": 35.83603835105896,
        "progress": {"num_of_steps": 4, "step": 4},
        "links": [{"href": "http://example.com/out", "rel": "alternate"}],
    }

    data = MockResp(200, json_data=sample, text="ok").json()
    info = actinia.parse_actinia_job(
        "96ed4cb9-1290-4409-b034-c162759c10a1",
        data,
    )
    # finished maps to 'successful'
    assert info["status"] == "successful"
    assert info["finished"] == "2026-01-06T11:02:49+00:00"
    # finished status should set progress to 100
    assert info["progress"] == 100


@pytest.mark.unittest
def test_map_status_and_reverse():
    """Test mapping between actinia raw status and OGC status values."""
    # forward mapping (actinia -> OGC)
    assert actinia.map_status("finished") == "successful"
    assert actinia.map_status("error") == "failed"
    assert actinia.map_status(None) == "accepted"

    # reverse mapping (OGC -> actinia)
    assert actinia.map_status_reverse("successful") == "finished"
    assert actinia.map_status_reverse("failed") == "error"
    assert actinia.map_status_reverse("dismissed") == "terminated"
    assert actinia.map_status_reverse("unknown") is None
