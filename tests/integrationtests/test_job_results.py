#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import pytest
from flask import Response

from tests.testsuite import TestCase

import email

job_id_single_stdout = "037f2417-8c6e-423f-8e57-f38ac5f50b67"
job_id_multiple_stdout = "b1d5702c-87d6-490d-ad1f-5edd792c8720"
job_id_single_export="8c88e3aa-3ba2-4050-9c2f-b3ad0a60f880"
job_id_multiple_export = "20d5b068-02ee-4791-805d-d0fc63c6c8c4"
job_id_file_export = "5af91732-7c71-481b-84c2-5dcc40dd0968"
job_id_export_and_stdout = "54384c50-5dd3-4179-aef5-f3110b1bf12c"
job_id_failed = "a04d145e-4073-4c33-8f76-5b160a20d05c"

def parse_multipart_related(data: bytes):
    msg = email.message_from_bytes(data, policy=email.policy.default)
    parts = {
        "content_type": list(),
        "content_id": list(),
        "content_location": list(),
    }
    for part in msg.iter_parts():
        parts["content_type"].append(part.get_content_type())
        parts["content_id"].append(part.get("Content-ID", ""))
        if part.get("Content-Location", ""):
            parts["content_location"].append(part.get("Content-Location", ""))
    return parts

class JobResultsTest(TestCase):
    """Test class for getting job results.

    For /jobs/<job_id>/results endpoint.
    """

    @pytest.mark.integrationtest
    def test_get_job_results_document_export_and_stdout(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_export_and_stdout}/results?"
                "resultResponse=document&"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert hasattr(resp, "json")
        resp_keys = list(resp.json.keys())
        resp_values =  list(resp.json.values())
        # check exemplary exported output: gpkg as zip with href link
        assert resp_keys[0] == "exporter_1_hospitals_cumberland_vector_GPKG"
        assert "href" in resp_values[0]
        assert resp_values[0]["type"] == "application/zip"

    @pytest.mark.integrationtest
    def test_get_job_results_document_export_file(self) -> None:
        # Job with file export generated from GRASS GIS module
        # (value with $file::unique_id)
        resp = self.app.get(
            (
                f"/jobs/{job_id_file_export}/results?"
                "resultResponse=document&"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200

    @pytest.mark.integrationtest
    def test_get_job_results_raw_reference_only_stdout(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_multiple_stdout}/results?resultResponse=raw&"
                "transmissionMode=reference"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 422
        assert resp.json["message"] == (
            "Format resultResponse=raw and "
            "transmissionMode=reference not supported for current "
            "job results. Use e.g. transmissionMode=value."
        )

    @pytest.mark.integrationtest
    def test_get_job_results_raw_reference_export_and_stdout(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_export_and_stdout}/results?resultResponse=raw&"
                "transmissionMode=reference"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 422
        assert resp.json["message"] == (
            "Format resultResponse=raw and "
            "transmissionMode=reference not supported for current "
            "job results. Use e.g. transmissionMode=mixed."
        )

    @pytest.mark.integrationtest
    def test_get_job_results_raw_reference_only_export(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_multiple_export}/results?resultResponse=raw&"
                "transmissionMode=reference"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        # Return empty body with two comma separated links in header
        assert resp.status_code == 204
        assert resp.data == b""
        assert resp.headers.get("Link") is not None
        assert len(resp.headers.get("Link").split(",")) == 2

    @pytest.mark.integrationtest
    def test_get_job_results_raw_value_single_export(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_single_export}/results?resultResponse=raw&"
                "transmissionMode=value"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert hasattr(resp, "data")
        # Return tif as binary
        assert len(resp.data) == 564649

    @pytest.mark.integrationtest
    def test_get_job_results_raw_value_single_stdout(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_single_stdout}/results?resultResponse=raw&"
                "transmissionMode=value"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert hasattr(resp, "data")
        assert resp.data == (
                b'["aspect","basin_50K","elevation",'
                b'"landuse96_28m","lsat7_2002_10","slope"]\n'
        )

    @pytest.mark.integrationtest
    def test_get_job_results_raw_value_multiple_export(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_multiple_export}/results?resultResponse=raw&"
                "transmissionMode=value"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 422
        assert resp.json["message"] == (
            "Format resultResponse=raw and "
            "transmissionMode=value not supported for current "
            "job results. Use e.g. transmissionMode=reference."
        )

    @pytest.mark.integrationtest
    def test_get_job_results_raw_value_export_and_stdout(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_export_and_stdout}/results?resultResponse=raw&"
                "transmissionMode=value"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 422
        assert resp.json["message"] == (
            "Format resultResponse=raw and "
            "transmissionMode=value not supported for current "
            "job results. Use e.g. transmissionMode=mixed."
        )

    @pytest.mark.integrationtest
    def test_get_job_results_raw_value_multiple_stdout(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_multiple_stdout}/results?resultResponse=raw&"
                "transmissionMode=value"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert resp.content_type == "multipart/related"
        assert hasattr(resp, "data")
        parts = parse_multipart_related(resp.data)
        # Return only plain/json stdout as multipart-content
        assert "text/plain" in parts["content_type"]
        assert "text/json" in parts["content_type"]
        assert not parts["content_location"]

    @pytest.mark.integrationtest
    def test_get_job_results_raw_mixed_only_export(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_multiple_export}/results?resultResponse=raw&"
                "transmissionMode=mixed"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert hasattr(resp, "data")
        # Return only reference links as multipart-content
        assert resp.content_type == "multipart/related"
        parts = parse_multipart_related(resp.data)
        assert "message/external-body" in parts["content_type"]
        assert parts["content_location"]
        assert "text/plain" not in parts["content_type"]

        # Check default values for response and transmissionMode
        # => should be same as above resp
        resp_job_default = self.app.get(
            f"/jobs/{job_id_multiple_export}/results",
            headers=self.HEADER_AUTH,
        )
        assert resp.status_code == resp_job_default.status_code
        assert resp.content_type == resp_job_default.content_type
        parts_job_default = parse_multipart_related(resp_job_default.data)
        assert parts == parts_job_default

    @pytest.mark.integrationtest
    def test_get_job_results_raw_mixed_only_stdout(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_multiple_stdout}/results?resultResponse=raw&"
                "transmissionMode=mixed"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert hasattr(resp, "data")
        assert resp.content_type == "multipart/related"
        parts = parse_multipart_related(resp.data)
        # Return only plain/json stdout as multipart-content
        assert "text/plain" in parts["content_type"]
        assert "text/json" in parts["content_type"]
        assert not parts["content_location"]

    @pytest.mark.integrationtest
    def test_get_job_results_raw_mixed_export_and_stdout(self) -> None:
        resp = self.app.get(
            (
                f"/jobs/{job_id_export_and_stdout}/results?resultResponse=raw&"
                "transmissionMode=mixed"
            ),
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 200
        assert hasattr(resp, "data")
        assert resp.content_type == "multipart/related"
        parts = parse_multipart_related(resp.data)
        # Return both: reference links + json stdout as multipart-content
        assert "text/json" in parts["content_type"]
        assert "message/external-body" in parts["content_type"]
        assert parts["content_location"]

    @pytest.mark.integrationtest
    def test_get_job_results_failed_job(self) -> None:
        resp = self.app.get(
            f"/jobs/{job_id_failed}/results",
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 400
        assert hasattr(resp, "json")
        assert "type" in resp.json
        assert resp.json["type"] == "AsyncProcessError"

    @pytest.mark.integrationtest
    def test_get_job_results_missing_auth(self) -> None:
        """Request without auth returns 401."""
        resp = self.app.get(f"/jobs/{job_id_export_and_stdout}/results")
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "Authentication required"

    @pytest.mark.integrationtest
    def test_get_job_results_false_auth(self) -> None:
        """Wrong credentials return 401 and error message."""
        resp = self.app.get(
            f"/jobs/{job_id_export_and_stdout}/results",
            headers=self.HEADER_AUTH_WRONG,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 401
        assert hasattr(resp, "json")
        assert "message" in resp.json
        assert resp.json["message"] == "ERROR: Unauthorized Access"

    @pytest.mark.integrationtest
    def test_get_job_results_not_found(self) -> None:
        """Non-existent job id returns 404 with OGC exception type."""
        resp = self.app.get(
            "/jobs/invalid_job_id/results",
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

    @pytest.mark.integrationtest
    def test_get_job_method_not_allowed(self) -> None:
        """Other methods than GET return 405 Method Not Allowed."""
        resp = self.app.post(
            f"/jobs/{job_id_export_and_stdout}/results",
            headers=self.HEADER_AUTH,
        )
        assert isinstance(resp, Response)
        assert resp.status_code == 405
        assert hasattr(resp, "json")
