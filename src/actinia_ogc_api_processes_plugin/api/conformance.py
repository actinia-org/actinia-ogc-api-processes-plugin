#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

OGC API Conformance endpoint class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Anika Weinmann"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response
from flask_restful_swagger_2 import Resource

from actinia_ogc_api_processes_plugin.authentication import require_basic_auth


class Conformance(Resource):
    """Conformance handling."""

    def __init__(self) -> None:
        self.msg = "Return conformance classes"

    @require_basic_auth()
    def get(self):
        """Return conformance classes for this plugin."""
        conforms = {
            "conformsTo": [
                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
                "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/job-list",
                "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/dismiss",
                "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json",
            ],
        }
        return make_response(jsonify(conforms), 200)
