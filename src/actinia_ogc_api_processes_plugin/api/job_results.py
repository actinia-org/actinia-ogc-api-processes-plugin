#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

JobResults endpoint implementation.
"""
from __future__ import annotations

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


from flask import jsonify, make_response, request
from flask_restful_swagger_2 import Resource, swagger
from requests.exceptions import ConnectionError as req_ConnectionError

from actinia_ogc_api_processes_plugin.apidocs import job_results
from actinia_ogc_api_processes_plugin.authentication import require_basic_auth
from actinia_ogc_api_processes_plugin.core.job_status_info import (
    get_actinia_job,
    get_job_status_info
)
from actinia_ogc_api_processes_plugin.api.job_status_info import JobStatusInfo
from actinia_ogc_api_processes_plugin.core.job_results import get_results
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
    StatusInfoResponseModel,
)
from actinia_ogc_api_processes_plugin.resources.logging import log


class JobResults(Resource):
    """JobResults handling."""

    def __init__(self) -> None:
        """Initialise."""
        self.msg = "Return job results"

    @require_basic_auth()
    @swagger.doc(job_results.describe_job_result_get_docs)
    def get(self, job_id):
        """Return job results for a given job id."""
        try:
            # read optional resultResponse parameter
            resultResponse = request.args.get("resultResponse") or None
            if resultResponse and (resultResponse != "raw" and resultResponse != "document"):
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=400,
                        message="ERROR: resultResponse must be 'raw' or 'document'",
                    ),
                )
                return make_response(res, 400)
            # read optional transmissionMode parameter
            transmissionMode = request.args.get("transmissionMode") or None
            if transmissionMode and (transmissionMode != "value" and transmissionMode != "reference" and transmissionMode != "mixed"):
                res = jsonify(
                                SimpleStatusCodeResponseModel(
                        status=400,
                        message="ERROR: transmissionMode must be 'value', 'reference' or 'mixed'",
                    ),
                )
                return make_response(res, 400)

            status_code, status_info, resp = get_job_status_info(job_id)
            if status_code == 200:
                if status_info["status"] == "successful":
                    # res, status_code = get_results(resp, resultResponse, transmissionMode)
                    # return make_response(res, status_code)
                    return get_results(resp, resultResponse, transmissionMode)
                elif status_info["status"] == "failed":
                    failure_status_code = 400 # return code from actinia, see also get_job_status_info() from core.job_status_info
                    res = jsonify(
                        {
                            "type": "AsyncProcessError", # todo: use valid type following OpenAPI 3.0 schema exception.yaml (RFC7807)
                            "title": "Job failed",
                            "status": failure_status_code,
                            "detail": f"Job '{job_id}' failed: {status_info["message"]}",
                            # "instance": TODO -> full actinia log url -> see also todo within core.job_results.get_results()
                            #                     here or/and within job_status_info?
                        },
                    )
                    return make_response(res, failure_status_code)
                else:
                    res = jsonify(
                        {
                            "type": (
                                "http://www.opengis.net/def/exceptions/"
                                "ogcapi-processes-1/1.0/result-not-ready"
                            ),
                            "title": "Result not ready",
                            "status": 404,
                            "detail": f"Results of job '{job_id}' not ready",
                        },
                    )
                    return make_response(res, 404)
            if status_code == 401:
                log.error("ERROR: Unauthorized Access")
                log.debug(f"actinia response: {getattr(resp, 'text', '')}")
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=401,
                        message="ERROR: Unauthorized Access",
                    ),
                )
                return make_response(res, 401)
            if status_code in {400, 404}:
                 log.error("ERROR: No such job")
                 log.debug(f"actinia response: {getattr(resp, 'text', '')}")
                 return JobStatusInfo._not_found_response(job_id)
            # fallback
            log.error("ERROR: Internal Server Error")
            code = getattr(resp, "status_code", status_code)
            text = getattr(resp, "text", "")
            log.debug(f"actinia status code: {code}")
            log.debug(f"actinia response: {text}")
            res = jsonify(
                SimpleStatusCodeResponseModel(
                    status=500,
                    message="ERROR: Internal Server Error",
                ),
            )
            return make_response(res, 500)
        except req_ConnectionError as e:
            log.error(f"Connection ERROR: {e}")
            res = jsonify(
                SimpleStatusCodeResponseModel(
                    status=503,
                    message=f"Connection ERROR: {e}",
                ),
            )
            return make_response(res, 503)
