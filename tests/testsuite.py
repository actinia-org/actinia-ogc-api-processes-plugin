#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2018-2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Base class for GRASS GIS REST API tests
"""

from __future__ import annotations

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika, Sören Gebbert"
__copyright__ = "Copyright 2018-2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

import unittest

from actinia_cloudevent_plugin.main import flask_app


class TestCase(unittest.TestCase):
    """Test case class."""

    URL_PREFIX = "http://localhost:5000/api/v1"

    def setUp(self) -> None:
        """Overwrite method setUp from unittest.TestCase class."""
        self.app_context = flask_app.app_context()
        self.app_context.push()
        # from http://flask.pocoo.org/docs/0.12/api/#flask.Flask.test_client:
        # Note that if you are testing for assertions or exceptions in your
        # application code, you must set app.testing = True in order for the
        # exceptions to propagate to the test client.  Otherwise, the exception
        # will be handled by the application (not visible to the test client)
        # and the only indication of an AssertionError or other exception will
        # be a 500 status code response to the test client.
        flask_app.testing = True
        self.app = flask_app.test_client()

    def tearDown(self) -> None:
        """Overwrite method tearDown from unittest.TestCase class."""
        self.app_context.pop()
