#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2018-2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Add endpoints to flask app with endpoint definitions and routes
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika, Anika Weinmann"
__copyright__ = "Copyright 2018-2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask_restful_swagger_2 import Api

from actinia_ogc_api_processes_plugin.api.process_list import ProcessList
from actinia_ogc_api_processes_plugin.api.process_description import (
    ProcessDescription,
)


def create_endpoints(flask_api: Api) -> None:
    """Create plugin endpoints."""
    apidoc = flask_api

    # Endpoints following: https://docs.ogc.org/is/18-062r2/18-062r2.html#toc0

    apidoc.add_resource(ProcessList, "/processes")
    apidoc.add_resource(ProcessDescription, "/processes/<string:processID>")
