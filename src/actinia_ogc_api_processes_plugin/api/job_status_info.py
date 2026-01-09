#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

JobStatusInfo endpoint implementation.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response
from flask_restful_swagger_2 import Resource, swagger
from requests.exceptions import ConnectionError as req_ConnectionError

from actinia_ogc_api_processes_plugin.apidocs import job_status_info
from actinia_ogc_api_processes_plugin.authentication import require_basic_auth
from actinia_ogc_api_processes_plugin.core.job_status_info import (
    get_job_status_info,
)
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
    StatusInfoResponseModel,
)
from actinia_ogc_api_processes_plugin.resources.logging import log


class JobStatusInfo(Resource):
    """JobStatusInfo handling."""

    def __init__(self) -> None:
        """Initialise."""
        self.msg = "Return job status information"

    @require_basic_auth()
    @swagger.doc(job_status_info.describe_job_status_info_get_docs)
    def get(self, job_id):
        """Return status information for a given job id."""
        try:
            status, status_info, resp = get_job_status_info(job_id)
            if status == 200:
                # build StatusInfoResponseModel from status_info dict
                model_kwargs = {}
                for k in (
                    "processID",
                    "type",
                    "jobID",
                    "status",
                    "message",
                    "created",
                    "started",
                    "finished",
                    "updated",
                    "progress",
                    "links",
                ):
                    if k in status_info:
                        model_kwargs[k] = status_info[k]

                res = jsonify(StatusInfoResponseModel(**model_kwargs))
                return make_response(res, 200)
            elif status == 401:
                log.error("ERROR: Unauthorized Access")
                log.debug(f"actinia response: {resp.text}")
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=401,
                        message="ERROR: Unauthorized Access",
                    ),
                )
                return make_response(res, 401)
            elif status in {400, 404}:
                log.error("ERROR: No such job")
                log.debug(f"actinia response: {resp.text}")
                res = jsonify(
                    {
                        "type": (
                            "http://www.opengis.net/def/exceptions/"
                            "ogcapi-processes-1/1.0/no-such-job"
                        ),
                        "title": "No Such Job",
                        "status": 404,
                        "detail": f"Job '{job_id}' not found",
                    },
                )
                return make_response(res, 404)
            else:
                log.error("ERROR: Internal Server Error")
                code = getattr(resp, "status_code", status)
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
