#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2018-2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Add endpoints to flask app with endpoint definitions and routes
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika, Anika Weinmann"
__copyright__ = "Copyright 2018-2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask_restful_swagger_2 import Api

from actinia_ogc_api_processes_plugin.api.job_list import JobList
from actinia_ogc_api_processes_plugin.api.job_status_info import JobStatusInfo
from actinia_ogc_api_processes_plugin.api.landing_page import LandingPage
from actinia_ogc_api_processes_plugin.api.process_description import (
    ProcessDescription,
)
from actinia_ogc_api_processes_plugin.api.process_list import ProcessList


def create_endpoints(flask_api: Api) -> None:
    """Create plugin endpoints."""
    app = flask_api.app
    apidoc = flask_api

    # Endpoints following: https://docs.ogc.org/is/18-062r2/18-062r2.html#toc0

    @app.route("/api")
    def api_endpoint():
        # flask_restful_swagger_2 appends api_spec_url always with .json:
        # map /api.json to /api
        return app.test_client().get("/api.json")

    apidoc.add_resource(LandingPage, "/")
    apidoc.add_resource(JobList, "/jobs")
    apidoc.add_resource(JobStatusInfo, "/jobs/<string:job_id>")
    apidoc.add_resource(ProcessList, "/processes")
    apidoc.add_resource(ProcessDescription, "/processes/<string:process_id>")
