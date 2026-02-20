#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Process Execution class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response
from flask_restful_swagger_2 import Resource, request, swagger
from requests.exceptions import ConnectionError  # noqa: A004

from actinia_ogc_api_processes_plugin.apidocs import process_execution
from actinia_ogc_api_processes_plugin.authentication import require_basic_auth
from actinia_ogc_api_processes_plugin.core.actinia_common import (
    safe_parse_actinia_job,
)
from actinia_ogc_api_processes_plugin.core.process_execution import (
    generate_new_joblinks,
    post_process_execution,
)
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)
from actinia_ogc_api_processes_plugin.resources.logging import log


class ProcessExecution(Resource):
    """ProcessExecution handling."""

    @require_basic_auth()
    @swagger.doc(process_execution.describe_process_execution_post_docs)
    def post(self, process_id):
        """ProcessExecution post method.

        Execute a process for the given process_id.
        """
        try:
            postbody = request.json
            resp = post_process_execution(process_id, postbody)
            if resp.status_code == 200:
                job_id, status_info = safe_parse_actinia_job(resp.json())
                if job_id not in status_info.get("links"):
                    status_info["links"] = generate_new_joblinks(job_id)
                return make_response(status_info, 201)
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
                # The content of that response SHALL be based upon
                # the OpenAPI 3.0 schema exception.yaml.
                # https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/schemas/exception.yaml
                # The type of the exception SHALL be:
                # “http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-process”.
                res = jsonify(
                    {
                        "type": "http://www.opengis.net/def/exceptions/"
                        "ogcapi-processes-1/1.0/no-such-process",
                        "title": "No Such Process",
                        "status": 404,
                        "detail": f"Process '{process_id}' not found",
                    },
                )
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
            log.error(f"Connection ERROR: {e}")
            res = jsonify(
                SimpleStatusCodeResponseModel(
                    status=503,
                    message=f"Connection ERROR: {e}",
                ),
            )
            return make_response(res, 503)
