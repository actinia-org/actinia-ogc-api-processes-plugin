#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Landing page class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Anika Weinmann"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response, request
from flask_restful_swagger_2 import Resource, swagger

from actinia_ogc_api_processes_plugin.apidocs import landing_page
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)


class LandingPage(Resource):
    """LandingPage handling."""

    def __init__(self) -> None:
        """LandingPage class initialisation."""
        self.msg = "Return landing page"

    @swagger.doc(landing_page.describe_landing_page_get_docs)
    def get(self):
        """LandingPage get method.

        Returns landing page.
        """
        base = request.url_root.rstrip("/")
        links = [
            {
                "href": f"{base}/?f=application/json",
                "rel": "self",
                "type": "application/json",
                "title": "This document (landing page) as JSON",
            },
            {
                "href": f"{base}/api.json",
                "rel": "service-desc",
                "type": "application/json",
                "title": "API definition for this endpoint as JSON",
            },
            {
                "href": f"{base}/api",
                "rel": "service-doc",
                "type": "application/json",
                "title": "API documentation (human-readable)",
            },
            {
                "href": f"{base}/conformance",
                "rel": "http://www.opengis.net/def/rel/ogc/1.0/conformance",
                "type": "application/json",
                "title": "Conformance declaration",
            },
            {
                "href": f"{base}/processes",
                "rel": "http://www.opengis.net/def/rel/ogc/1.0/processes",
                "type": "application/json",
                "title": "Processes collection",
            },
            {
                "href": f"{base}/jobs",
                "rel": "http://www.opengis.net/def/rel/ogc/1.0/job-list",
                "type": "application/json",
                "title": "Jobs collection",
            },
        ]
        landing = {
            "title": "actinia OGC API - Processes plugin",
            "description": "OGC API landing page exposing available "
            "resources.",
            "links": links,
        }
        return make_response(jsonify(landing), 200)

    def post(self) -> SimpleStatusCodeResponseModel:
        """LandingPage post method: not allowed response."""
        res = jsonify(
            SimpleStatusCodeResponseModel(
                status=405,
                message="Method Not Allowed",
            ),
        )
        return make_response(res, 405)
