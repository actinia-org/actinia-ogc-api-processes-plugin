#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import pytest
from flask import Response

from tests.testsuite import TestCase


class JobListTest(TestCase):
    """Integration tests for /jobs endpoint."""

    @pytest.mark.integrationtest
    def test_get_jobs(self) -> None:
        """Successful GET /jobs returns job list."""
        resp = self.app.get("/jobs", headers=self.HEADER_AUTH)
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert hasattr(resp, "json")

        assert "jobs" in resp.json
        assert "links" in resp.json
        if resp.json.get("jobs"):
            first = resp.json["jobs"][0]
            assert "jobID" in first
            assert "status" in first
            assert "links" in first

    @pytest.mark.integrationtest
    def test_get_jobs_missing_auth(self) -> None:
        """Request without auth returns 401."""
        resp = self.app.get("/jobs")
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Authentication required"

    @pytest.mark.integrationtest
    def test_get_jobs_false_auth(self) -> None:
        """Wrong credentials return 401 and error message."""
        resp = self.app.get("/jobs", headers=self.HEADER_AUTH_WRONG)
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "ERROR: Unauthorized Access"

    @pytest.mark.integrationtest
    def test_post_jobs_method_not_allowed(self) -> None:
        """POST to /jobs is not allowed."""
        resp = self.app.post("/jobs")
        assert isinstance(resp, Response)
        assert resp.status_code == 405
        assert hasattr(resp, "json")
        assert "message" in resp.json
