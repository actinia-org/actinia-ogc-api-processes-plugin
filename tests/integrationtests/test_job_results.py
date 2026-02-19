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

def parse_multipart_related(data: bytes):
    msg = email.message_from_bytes(data, policy=email.policy.default)
    parts = []
    for part in msg.iter_parts():
        parts.append(
            {
                "content_type": part.get_content_type(),
                "content_id": part.get('Content-ID', ''),
            }
        )
    return parts

class JobResultsTest(TestCase):
    """Test class for getting job results.

    For /jobs/<job_id>/results endpoint.
    """

    """
    single stdout:                          2812bfd7-eea3-470b-8d33-15fbd09da14e
    multiple stdout (list, kv, table):       c957286f-d4f2-45ec-a39e-b3077ceb6603
    
    gpkg u. shapefile export + stdout json: 0915fbd2-a985-4c88-9f5c-5abdee7027a2
    
    single (small) raster/epxort:            ba4e00c9-c4b7-4de0-aa72-6718d89aa414
    multiple raster/export:                  f9236db4-e471-4f6a-9a88-c821666aa802
    csv + txt export:                        b963fbc3-642e-4ffd-b344-f58eda164e68
    strds export:                           8de0645d-ebaf-48d6-bc02-b94bfe435df0
    geojson export:                         1d511068-803b-46bf-a718-7b4fa9c6d0b9
    
    # default values -> mixed + raw
    """

    @pytest.mark.integrationtest
    def test_get_job_results_raw_value(self) -> None:

        # -- Single export (tif)
        job_id_single_export="ba4e00c9-c4b7-4de0-aa72-6718d89aa414"
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
        # returned tif as binary
        assert len(resp.data) == 564649

        # -- Single (list) stdout
        job_id_single_stdout = "2812bfd7-eea3-470b-8d33-15fbd09da14e"
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

        # -- Multiple export
        job_id_multiple_export = "f9236db4-e471-4f6a-9a88-c821666aa802"
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

        # -- Both: export (gpkg + shapefile) and stdout (json)
        job_id_stdout_and_export = "0915fbd2-a985-4c88-9f5c-5abdee7027a2"
        resp = self.app.get(
            (
                f"/jobs/{job_id_stdout_and_export}/results?resultResponse=raw&"
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

        # -- Multiple (list, kv, table) stdout
        job_id_multiple_stdout = "c957286f-d4f2-45ec-a39e-b3077ceb6603"
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
        # check for json vs plain return of stdout results
        assert parts[0]["content_id"] == "elevation_table"
        assert parts[0]["content_type"] == "text/plain"
        assert parts[2]["content_id"] == "region_kv"
        assert parts[2]["content_type"] == "text/json"

        
    @pytest.mark.integrationtest
    def test_get_job_results_raw_reference(self) -> None:

        # -- Only stdout
        job_id_multiple_stdout = "c957286f-d4f2-45ec-a39e-b3077ceb6603"
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

        # -- Mixed: gpkg a. shapefile export + stdout json
        job_id_mixed = "0915fbd2-a985-4c88-9f5c-5abdee7027a2"
        resp = self.app.get(
            (
                f"/jobs/{job_id_mixed}/results?resultResponse=raw&"
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
    def test_get_job_results_raw_mixed(self) -> None:

        # -- Multiple (list, kv, table) stdout
        job_id_multiple_stdout = "c957286f-d4f2-45ec-a39e-b3077ceb6603"
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
        # check for json vs plain return of stdout results
        assert parts[0]["content_id"] == "elevation_table"
        assert parts[0]["content_type"] == "text/plain"
        assert parts[2]["content_id"] == "region_kv"
        assert parts[2]["content_type"] == "text/json"

    # @pytest.mark.integrationtest
    # def test_get_job_results_document(self) -> None:
    #     # response=document
        # TODO
