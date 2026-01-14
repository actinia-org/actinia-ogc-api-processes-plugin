#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Integration tests for DELETE /jobs/<job_id> (cancel job).
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import pytest
from flask import Response

from tests.testsuite import TestCase


class JobStatusInfoDeleteTest(TestCase):
    """Integration tests for /jobs/<job_id> endpoint."""

    # # Can only be activated when example job is available in actinia instance
    # @pytest.mark.integrationtest
    # def test_delete_job_status_success(self) -> None:
    #     """Successful query returns statusInfo-like structure."""
    #     # example job id used in response model examples
    #     job_id = "d63dcd9e-4914-4989-a47e-c9de722a63ab"
    #     resp = self.app.delete(f"/jobs/{job_id}", headers=self.HEADER_AUTH)
    #     assert isinstance(resp, Response)
    #     assert resp.status_code == 200
    #     assert hasattr(resp, "json")
    #     assert "jobID" in resp.json, "There is no 'jobID' in response"
    #     assert "status" in resp.json, "There is no 'status' in response"
    #     assert "type" in resp.json, "There is no 'type' in response"
    #     assert "links" in resp.json, "There is no 'links' in response"
    #     assert resp.json["status"] == "dismissed"

    @pytest.mark.integrationtest
    def test_delete_job_status_missing_auth(self) -> None:
        """Request without auth returns 401."""
        job_id = "d63dcd9e-4914-4989-a47e-c9de722a63ab"
        resp = self.app.delete(f"/jobs/{job_id}")
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Authentication required"

    @pytest.mark.integrationtest
    def test_get_job_status_false_auth(self) -> None:
        """Wrong credentials return 401 and error message."""
        job_id = "d63dcd9e-4914-4989-a47e-c9de722a63ab"
        resp = self.app.delete(
            f"/jobs/{job_id}",
            headers=self.HEADER_AUTH_WRONG,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "ERROR: Unauthorized Access"

    @pytest.mark.integrationtest
    def test_get_job_status_not_found(self) -> None:
        """Non-existent job id returns 404 with OGC exception type."""
        resp = self.app.delete(
            "/jobs/invalid_job_id",
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 404
        assert hasattr(resp, "json")
        assert "type" in resp.json
        expected = (
            "http://www.opengis.net/def/exceptions/"
            "ogcapi-processes-1/1.0/no-such-job"
        )
        assert resp.json["type"] == expected
