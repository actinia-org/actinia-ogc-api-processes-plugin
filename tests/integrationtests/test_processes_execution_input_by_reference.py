#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Anika Weinmann"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import json
import pathlib

import pytest
from flask import Response

from tests.testsuite import TestCase

test_process_input_error = {
    "inputs": {
        "input": {
            "href": "https://raw.githubusercontent.com/mmacata/pagestest/"
            "refs/heads/gh-pages/kalimantan_osm_epsg4326.geojson",
        },
        "size": 3,
        "method": ["maximum"],
        "output": ["slope_n3_max"],
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}


class ProcessExecutionInputByReference(TestCase):
    """Test class for executing Processes with input by reference.

    For /processes/<process_id>/execute endpoint.
    """

    @pytest.mark.integrationtest
    def test_post_process_execution_vbuffer(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Succesfull query v.buffer process
        """
        json_path = (
            "tests/resources/request_bodies/test_v_buffer_by_reference.json"
        )
        with pathlib.Path(json_path).open(encoding="utf-8") as file:
            request_body = json.load(file)

        resp = self.app.post(
            "/processes/v.buffer/execution",
            headers=self.HEADER_AUTH,
            json=request_body,
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
    def test_post_process_execution_rneighbors(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Succesfull query r.neighbors process with input by reference
        """
        json_path = (
            "tests/resources/request_bodies/test_r_neighbors_by_reference.json"
        )
        with pathlib.Path(json_path).open(encoding="utf-8") as file:
            request_body = json.load(file)

        resp = self.app.post(
            "/processes/r.neighbors/execution",
            headers=self.HEADER_AUTH,
            json=request_body,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 201
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Resource accepted"

    @pytest.mark.integrationtest
    def test_post_process_execution_vclip(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Succesfull query v.clip process with input by reference
        """
        json_path = (
            "tests/resources/request_bodies/test_v_clip_by_reference.json"
        )
        with pathlib.Path(json_path).open(encoding="utf-8") as file:
            request_body = json.load(file)

        resp = self.app.post(
            "/processes/v.clip/execution",
            headers=self.HEADER_AUTH,
            json=request_body,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 201
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Resource accepted"

    @pytest.mark.integrationtest
    def test_post_process_execution_input_by_ref_error(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Failing query with input by reference
        """
        resp = self.app.post(
            "/processes/r.neighbors/execution",
            headers=self.HEADER_AUTH,
            json=test_process_input_error,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 400
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert "'.geojson' which is not supported." in resp.json["message"]
