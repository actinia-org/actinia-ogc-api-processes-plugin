#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Anika Weinmann"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import pytest
from flask import Response

from tests.testsuite import TestCase


class LandingPageTest(TestCase):
    """Processes test class for / endpoint."""

    CONFORMANCE_REL = "http://www.opengis.net/def/rel/ogc/1.0/conformance"

    @pytest.mark.integrationtest
    def test_get_landing_page(self) -> None:
        """Test the get method of the / endpoint.

        Succesfull query
        """
        resp = self.app.get("/")
        assert isinstance(
            resp,
            Response,
        ), "The response is not of type Response"
        assert (
            resp.status_code == 200
        ), f"The status code is not 200 but {resp.status_code}."
        assert hasattr(resp, "json"), "The response has no attribute 'json'"

        # -- test required attributes
        assert "links" in resp.json, "There is no 'links' inside the response"
        # -- test "service-desc" and/or "service-doc" link
        links = resp.json["links"]
        assert any(item.get("rel") == "service-doc" for item in links) or any(
            item.get("rel") == "service-doc" for item in links
        ), "No 'service-desc' or 'service-doc' in links"
        # -- test conformance class declaration
        assert any(
            item.get("rel") == self.CONFORMANCE_REL for item in links
        ), (
            "Conformance class declaration is not linked as "
            f"'{self.CONFORMANCE_REL}'"
        )
        # -- test “processes” link
        assert any(
            item.get("href").endswith("/processes") for item in links
        ), "No link to '/processes' endpoint"
        # -- test "jobs" link
        assert any(
            item.get("href").endswith("/jobs") for item in links
        ), "No link to '/jobs' endpoint"
