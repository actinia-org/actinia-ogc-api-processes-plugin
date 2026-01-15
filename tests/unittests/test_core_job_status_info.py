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

from actinia_ogc_api_processes_plugin.core import job_status_info as core


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
def test_get_job_status_info_success_and_error(monkeypatch):
    """Test get_job_status_info function for success and error cases."""
    job_id = "job-123"
    sample = {
        "status": "finished",
        "resource_id": "proc-1",
        "accept_timestamp": 1609459200,
        "timestamp": 1609462800,
        "time_delta": 3600,
        "progress": {"num_of_steps": 4, "step": 2},
        "links": [{"href": "http://example.com/out", "rel": "alternate"}],
    }

    resp = MockResp(200, json_data=sample, text="ok")

    # patch the network call inside the module to return our mock
    monkeypatch.setattr(core, "get_actinia_job", lambda _jid: resp)

    status, status_info, r = core.get_job_status_info(job_id)
    assert status == 200
    assert r is resp
    assert status_info["jobID"] == job_id
    assert status_info["status"] == "successful"
    assert status_info["processID"] == "proc-1"
    assert status_info["created"] == "2021-01-01T00:00:00+00:00"
    assert status_info["updated"] == "2021-01-01T01:00:00+00:00"
    # finished == accept + time_delta
    assert status_info["finished"] == "2021-01-01T01:00:00+00:00"
    # status is 'finished' -> progress should be 100
    assert status_info["progress"] == 100
    assert isinstance(status_info["links"], list)

    # non-200 is passed through
    notfound = MockResp(404, json_data={}, text="not found")
    monkeypatch.setattr(core, "get_actinia_job", lambda _jid: notfound)
    status2, info2, r2 = core.get_job_status_info(job_id)
    assert status2 == 404
    assert info2 is None
    assert r2 is notfound
