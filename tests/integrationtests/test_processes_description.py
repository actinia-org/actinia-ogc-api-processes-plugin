#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import pytest
from flask import Response

from tests.testsuite import TestCase


class ProcessesDescriptionTest(TestCase):
    """Test class for describing Processes.

    For /processes/<process_id> endpoint.
    """

    @pytest.mark.integrationtest
    def test_get_processes(self) -> None:
        """Test the get method of the /processes/<process_id> endpoint.

        Succesfull query
        """
        resp = self.app.get("/processes/g.region", headers=self.HEADER_AUTH)
        assert isinstance(
            resp,
            Response,
        ), "The response is not of type Response"
        assert (
            resp.status_code == 200
        ), f"The status code is not 200 but {resp.status_code}."
        assert hasattr(resp, "json"), "The response has no attribute 'json'"

        #  check exemplary first entry of actinia response
        assert (
            "categories" in resp.json
        ), "There is no 'categories' inside the response"

    @pytest.mark.integrationtest
    def test_get_processes_invalid_process_id(self) -> None:
        """Test the get method of the /processes/<process_id> endpoint.

        With invalid (non existent) <process_id>
        """
        resp = self.app.get(
            "/processes/invalid_process_id",
            headers=self.HEADER_AUTH,
        )
        assert isinstance(
            resp,
            Response,
        ), "The response is not of type Response"
        assert (
            resp.status_code == 404
        ), f"The status code is not 404 but {resp.status_code}."
        assert hasattr(resp, "json"), "The response has no attribute 'json'"
        assert "type" in resp.json, "There is no 'type' inside the response"
        assert (
            resp.json["type"]
            == "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-process"
        ), (
            f"The response is wrong. '{resp.json['type']}',"
            "instead of 'http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-process'"
        )

    @pytest.mark.integrationtest
    def test_get_processes_false_auth(self) -> None:
        """Test the get method of the /processes/<process_id> endpoint.

        With wrong authentication
        """
        resp = self.app.get(
            "/processes/g.region",
            headers=self.HEADER_AUTH_WRONG,
        )
        assert isinstance(
            resp,
            Response,
        ), "The response is not of type Response"
        assert (
            resp.status_code == 401
        ), f"The status code is not 401 but {resp.status_code}."
        assert hasattr(resp, "json"), "The response has no attribute 'json'"
        assert (
            "message" in resp.json
        ), "There is no 'message' inside the response"
        assert resp.json["message"] == "ERROR: Unauthorized Access", (
            f"The response is wrong. '{resp.json['message']}',"
            "instead of ''ERROR: Unauthorized Access'"
        )

    @pytest.mark.integrationtest
    def test_get_processes_missing_auth(self) -> None:
        """Test the get method of the /processes/<process_id> endpoint.

        With missing authentication
        """
        resp = self.app.get("/processes/g.region")
        assert isinstance(
            resp,
            Response,
        ), "The response is not of type Response"
        assert (
            resp.status_code == 401
        ), f"The status code is not 401 but {resp.status_code}."
        assert hasattr(resp, "json"), "The response has no attribute 'json'"
        assert (
            "message" in resp.json
        ), "There is no 'message' inside the response"
        assert resp.json["message"] == "Authentication required", (
            f"The response is wrong. '{resp.json['message']}',"
            "instead of 'Authentication required'"
        )
