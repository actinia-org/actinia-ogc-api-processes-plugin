#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Process List class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response
from flask_restful_swagger_2 import Resource, swagger

from actinia_ogc_api_processes_plugin.authentication import require_basic_auth

from actinia_ogc_api_processes_plugin.apidocs import processlist
from actinia_ogc_api_processes_plugin.core.processlist import get_modules
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)
from actinia_ogc_api_processes_plugin.resources.logging import log


class ProcessList(Resource):
    """ProcessList handling."""

    def __init__(self) -> None:
        """ProcessList class initialisation."""
        self.msg = (
            "TODO"
        )

    @require_basic_auth()
    @swagger.doc(processlist.describe_processlist_get_docs)
    def get(self):
        """ProcessList get method.

        Returns process list with process identifiers
        and link to process descriptions.
        """
        resp, status_code_grass_modules, status_code_actinia_modules = get_modules()
        if status_code_grass_modules == 200 and status_code_actinia_modules == 200:
            return make_response(resp, 200)
        elif status_code_grass_modules == 401 or status_code_actinia_modules == 401:
            log.error("ERROR: Unauthorized Access")
            log.debug(f"grass_modules status code: {status_code_grass_modules}")
            log.debug(f"actinia_modules status code: {status_code_actinia_modules}")
            log.debug(f"actinia response: {resp}")
            res = jsonify(
                SimpleStatusCodeResponseModel(
                    status=401,
                    message="ERROR: Unauthorized Access",
                ),
            )
            return make_response(res, 401)
        else:
            log.error("ERROR: Internal Server Error")
            log.debug(f"grass_modules status code: {status_code_grass_modules}")
            log.debug(f"actinia_modules status code: {status_code_actinia_modules}")
            log.debug(f"actinia response: {resp}")
            res = jsonify(
                SimpleStatusCodeResponseModel(
                    status=500,
                    message="ERROR: Internal Server Error",
                ),
            )
            return make_response(res, 500)

    def post(self) -> SimpleStatusCodeResponseModel:
        """ProcessList post method: not allowed response."""
        res = jsonify(
            SimpleStatusCodeResponseModel(
                status=405,
                message="Method Not Allowed",
            ),
        )
        return make_response(res, 405)
