#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Process List class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response, request
from flask_restful_swagger_2 import Resource, swagger
from requests.exceptions import ConnectionError, Timeout

from actinia_ogc_api_processes_plugin.apidocs import process_description
from actinia_ogc_api_processes_plugin.authentication import require_basic_auth
from actinia_ogc_api_processes_plugin.core.process_description import get_module_description
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)
from actinia_ogc_api_processes_plugin.resources.logging import log


class ProcessDescription(Resource):
    """ProcessDescription handling."""

    def __init__(self) -> None:
        """ProcessDescription class initialisation."""
        self.msg = "Return process description"

    @require_basic_auth()
    @swagger.doc(process_description.describe_process_description_get_docs)
    def get(self, processID):
        """ProcessDescription get method.

        Returns process description for given processID.
        """
        try:
            resp = get_module_description(processID)
            if resp.status_code == 200:
                return make_response(jsonify(resp.json()), 200)
            elif resp.status_code == 401:
                log.error("ERROR: Unauthorized Access")
                log.debug(f"actinia response: {resp.text}")
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=401,
                        message="ERROR: Unauthorized Access",
                    ),
                )
                return make_response(res, 401)
            elif resp.status_code == 404:
                log.error("ERROR: No such process")
                log.debug(f"actinia response: {resp.text}")
                # If operation is executed using an invalid process identifier,
                # the response SHALL be HTTP status code 404.
                # The content of that response SHALL be based upon the OpenAPI 3.0 schema exception.yaml.
                # https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/schemas/exception.yaml
                # The type of the exception SHALL be “http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-process”.
                res = jsonify({
                    "type": "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-process",
                    "title": "No Such Process",
                    "status": 404,
                    "detail": f"Process '{processID}' not found"
                })
                return make_response(res, 404)
            else:
                log.error("ERROR: Internal Server Error")
                log.debug(f"actinia status code: {resp.status_code}")
                log.debug(f"actinia response: {resp.text}")
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=500,
                        message="ERROR: Internal Server Error",
                    ),
                )
                return make_response(res, 500)
        except ConnectionError as e:
            log.error(f"Connection ERRO: {e}")
            res = jsonify(
                SimpleStatusCodeResponseModel(
                    status=503,
                    message=f"Connection ERROR: {e}",
                ),
            )
            return make_response(res, 503)
    

    def post(self, processID) -> SimpleStatusCodeResponseModel:
        """ProcessList post method: not allowed response."""
        res = jsonify(
            SimpleStatusCodeResponseModel(
                status=405,
                message="Method Not Allowed",
            ),
        )
        return make_response(res, 405)
