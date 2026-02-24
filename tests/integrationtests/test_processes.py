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


class ProcessesTest(TestCase):
    """Processes test class for /processes endpoint."""

    @pytest.mark.integrationtest
    def test_get_processes(self) -> None:
        """Test the get method of the /processes endpoint.

        Succesfull query
        """
        resp = self.app.get("/processes", headers=self.HEADER_AUTH)
        assert isinstance(
            resp,
            Response,
        ), "The response is not of type Response"
        assert (
            resp.status_code == 200
        ), f"The status code is not 200 but {resp.status_code}."
        assert hasattr(resp, "json"), "The response has no attribute 'json'"

        # -- test required attributes
        assert (
            "processes" in resp.json
        ), "There is no 'processes' inside the response"
        assert "links" in resp.json, "There is no 'links' inside the response"
        # check exemplary first processes entry
        assert (
            "id" in resp.json["processes"][0]
        ), "There is no 'id' inside 'processes'"
        assert (
            "version" in resp.json["processes"][0]
        ), "There is no 'version' inside 'processes'"
        # check exemplary first links entry
        assert (
            "href" in resp.json["links"][0]
        ), "There is no 'href' inside 'links'"

    @pytest.mark.integrationtest
    def test_get_processes_limit_parameter(self) -> None:
        """Test the get method of the /processes endpoint with limit.

        Succesfull query
        """
        resp = self.app.get(
            "/processes",
            query_string={"limit": 1},
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert hasattr(resp, "json")
        assert "processes" in resp.json
        assert len(resp.json["processes"]) == 1

    @pytest.mark.integrationtest
    def test_get_processes_wrong_limit_parameter(self) -> None:
        """Test the get method of the /processes endpoint with limit.

        Invalid limit value (string)
        """
        resp = self.app.get(
            "/processes",
            query_string={"limit": "abc"},
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 400
        assert hasattr(resp, "json")
        assert "message" in resp.json

    @pytest.mark.integrationtest
    def test_get_processes_wrong_limit_parameter_2(self) -> None:
        """Test the get method of the /processes endpoint with limit.

        Invalid limit value (string)
        """
        resp = self.app.get(
            "/processes",
            query_string={"limit": "20000"},
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 400
        assert hasattr(resp, "json")
        assert "message" in resp.json

    @pytest.mark.integrationtest
    def test_get_processes_missing_auth(self) -> None:
        """Test the get method of the /processes endpoint.

        With missing authentication
        """
        resp = self.app.get("/processes")
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

    @pytest.mark.integrationtest
    def test_get_processes_false_auth(self) -> None:
        """Test the get method of the /processes endpoint.

        With wrong authentication
        """
        resp = self.app.get("/processes", headers=self.HEADER_AUTH_WRONG)
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
    def test_post_processes(self) -> None:
        """Test the post method of the /processes endpoint."""
        resp = self.app.post("/processes")
        assert isinstance(
            resp,
            Response,
        ), "The response is not of type Response"
        assert (
            resp.status_code == 405
        ), f"The status code is not 405 but {resp.status_code}."
        assert hasattr(resp, "json"), "The response has no attribute 'json'"
        assert (
            "message" in resp.json
        ), "There is no 'message' inside the response"
        assert resp.json["message"] == "Method Not Allowed", (
            f"The response is wrong. '{resp.json['message']}',"
            "instead of 'Method Not Allowed'"
        )
