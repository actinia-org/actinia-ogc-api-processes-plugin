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

test_v_buffer = {
    "inputs": {
        "input": "boundary_county",
        "type": ["vector"],
        "output": "boundary_county_1_buf",
        "cats": "1",
        "distance": 2,
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}

test_v_buffer_array_error = {
    "inputs": {
        "input": "boundary_county",
        "output": "boundary_county_1_buf",
        "type": "vector",
        "cats": "1",
        "distance": 2,
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}

test_r_neighbors = {
    "inputs": {
        "input": "elevation",
        "size": 3,
        "method": ["maximum"],
        "output": ["elevation_n3_max"],
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}

test_g_region = {
    "inputs": {
        "raster": ["elevation"],
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}

test_v_overlay = {
    "inputs": {
        "ainput": "firestations",
        "binput": "nc_state",
        "operator": "and",
        "output": "test",
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
    "response": "document",
}


class ProcessExecutionGrassModule(TestCase):
    """Test class for executing Processes with GRASS modules.

    For /processes/<process_id>/execute endpoint.
    """

    @pytest.mark.integrationtest
    @pytest.mark.dev
    def test_post_process_execution_vbuffer(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Succesfull query v.buffer process
        """
        resp = self.app.post(
            "/processes/v.buffer/execution",
            headers=self.HEADER_AUTH,
            json=test_v_buffer,
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
    def test_post_process_execution_vbuffer_array_error(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Bad request query: v.buffer 'type' as string instead of array
        (defined as array within process description)
        """
        resp = self.app.post(
            "/processes/v.buffer/execution",
            headers=self.HEADER_AUTH,
            json=test_v_buffer_array_error,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 400
        assert "Input parameter 'type' should be array" in resp.json["message"]

    @pytest.mark.integrationtest
    def test_post_process_execution_rneighbors(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        Succesfull query r.neighbors module
        """
        resp = self.app.post(
            "/processes/r.neighbors/execution",
            headers=self.HEADER_AUTH,
            json=test_r_neighbors,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 201
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Resource accepted"

    @pytest.mark.integrationtest
    def test_post_process_execution_not_supported_module_1(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        With not supported module because of wrong GRASS processing type
        """
        resp = self.app.post(
            "/processes/g.region/execution",
            headers=self.HEADER_AUTH,
            json=test_g_region,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 400
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert (
            resp.json["message"] == "Process execution of <g.region> not "
            "supported."
        )

    @pytest.mark.integrationtest
    def test_post_process_execution_not_supported_module_2(self) -> None:
        """Test post method of the /processes/<process_id>/execution endpoint.

        With not supported module because of missing input parameter
        """
        resp = self.app.post(
            "/processes/v.overlay/execution",
            headers=self.HEADER_AUTH,
            json=test_v_overlay,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 400
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert (
            resp.json["message"] == "Process execution of <v.overlay> not "
            "supported."
        )
