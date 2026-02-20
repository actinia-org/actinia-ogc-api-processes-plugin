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


class ConformanceTest(TestCase):
    """Processes test class for /conformance endpoint."""

    @pytest.mark.integrationtest
    def test_get_conformance(self) -> None:
        """Test the get method of the /conformance endpoint.

        Succesfull query
        """
        resp = self.app.get("/conformance")
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
            "conformsTo" in resp.json
        ), "There is no 'conformsTo' inside the response"
