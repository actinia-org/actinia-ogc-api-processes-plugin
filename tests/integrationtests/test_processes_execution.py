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


class ProcessExecution(TestCase):
    """Test class for executing Processes.

    For /processes/<process_id>/execute endpoint.
    """

    @pytest.mark.integrationtest
    def test_post_process_execution(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Succesfull query
        """
        resp = self.app.post(
            "/processes/point_in_polygon/execution",
            headers=self.HEADER_AUTH,
            json={},
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 201
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Resource accepted"

    @pytest.mark.integrationtest
    def test_post_process_execution_invalid_process_id(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        With invalid (non existent) <process_id>
        """
        resp = self.app.post(
            "/processes/invalid_process_id/execution",
            headers=self.HEADER_AUTH,
            json={},
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 404
        assert hasattr(resp, "json")
        assert "type" in resp.json
        assert resp.json["type"] == (
            "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/"
            "no-such-process"
        )

    @pytest.mark.integrationtest
    def test_post_process_execution_false_auth(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        With wrong authentication
        """
        resp = self.app.post(
            "/processes/point_in_polygon/execution",
            headers=self.HEADER_AUTH_WRONG,
            json={},
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "ERROR: Unauthorized Access"

    @pytest.mark.integrationtest
    def test_post_process_execution_missing_auth(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        With missing authentication
        """
        resp = self.app.post(
            "/processes/point_in_polygon/execution",
            json={},
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Authentication required"
