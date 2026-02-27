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

test_process_input = {
    "inputs": {
        "url_to_geojson_point": "https://raw.githubusercontent.com/"
        "mmacata/pagestest/gh-pages/pointInBonn.geojson",
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}

test_process_input_bbox = {
    "inputs": {
        "url_to_geojson_point": "https://raw.githubusercontent.com/"
        "mmacata/pagestest/gh-pages/pointInBonn.geojson",
        "bounding_box": {"bbox": [6154000, 4464000, 6183000, 4490000]},
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}

test_process_input_bbox_error = {
    "inputs": {
        "url_to_geojson_point": "https://raw.githubusercontent.com/"
        "mmacata/pagestest/gh-pages/pointInBonn.geojson",
        "bounding_box": {"bbox": [6154000, 4464000]},
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}

test_process_input_with_grass_project = {
    "inputs": {
        "url_to_geojson_point": "https://raw.githubusercontent.com/"
        "mmacata/pagestest/gh-pages/pointInBonn.geojson",
        "project": "nc_spm_08",
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}


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
            json=test_process_input,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 201
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Resource accepted"
        # response should follow StatusInfoResponseModel:
        # contain jobID, status and links
        assert isinstance(resp.json, dict)
        assert "jobID" in resp.json
        assert "status" in resp.json
        assert resp.json["status"] in {
            "accepted",
            "running",
            "successful",
            "failed",
            "dismissed",
        }
        assert "links" in resp.json
        assert isinstance(resp.json["links"], list)
        # link should point to job status resource
        if resp.json["links"]:
            assert any(
                "/jobs/" in link.get("href", "") for link in resp.json["links"]
            )

    @pytest.mark.integrationtest
    def test_post_process_execution_with_grass_project(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Succesfull query
        """
        resp = self.app.post(
            "/processes/point_in_polygon/execution",
            headers=self.HEADER_AUTH,
            json=test_process_input_with_grass_project,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 201
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Resource accepted"

    @pytest.mark.integrationtest
    def test_post_process_execution_with_bbox(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Succesfull query with bbox
        """
        resp = self.app.post(
            "/processes/point_in_polygon/execution",
            headers=self.HEADER_AUTH,
            json=test_process_input_bbox,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 201
        assert hasattr(resp, "json")
        assert "message" in resp.json

    @pytest.mark.integrationtest
    @pytest.mark.dev
    def test_post_process_execution_with_bbox_error(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Failing query with bbox
        """
        resp = self.app.post(
            "/processes/point_in_polygon/execution",
            headers=self.HEADER_AUTH,
            json=test_process_input_bbox_error,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 400
        assert hasattr(resp, "json")
        assert "type" in resp.json
        assert "bounding_box" in resp.json["message"]

    @pytest.mark.integrationtest
    def test_post_process_execution_invalid_process_id(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        With invalid (non existent) <process_id>
        """
        resp = self.app.post(
            "/processes/invalid_process_id/execution",
            headers=self.HEADER_AUTH,
            json=test_process_input,
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
            json=test_process_input,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        # simple status response: check status code and message presence
        assert resp.json.get("status") == 401 or "Unauthorized" in str(
            resp.json.get("message", ""),
        )

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
        # simple status response: check status code and message presence
        assert resp.json.get("status") == 401 or "Authentication" in str(
            resp.json.get("message", ""),
        )
