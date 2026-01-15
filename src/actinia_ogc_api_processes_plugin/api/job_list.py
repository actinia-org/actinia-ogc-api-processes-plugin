#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

JobList endpoint implementation.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response
from flask_restful_swagger_2 import Resource, swagger
from requests.exceptions import ConnectionError as req_ConnectionError

from actinia_ogc_api_processes_plugin.apidocs import job_list
from actinia_ogc_api_processes_plugin.authentication import require_basic_auth
from actinia_ogc_api_processes_plugin.core.job_list import (
    get_actinia_jobs,
    parse_actinia_jobs,
)
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)
from actinia_ogc_api_processes_plugin.resources.logging import log


class JobList(Resource):
    """JobList handling."""

    def __init__(self) -> None:
        """Initialise."""
        self.msg = "Return job list for current user"

    @require_basic_auth()
    @swagger.doc(job_list.describe_job_list_get_docs)
    def get(self):
        """Return a list of jobs for the authenticated user."""
        try:
            resp = get_actinia_jobs()
            if resp.status_code == 200:
                jobs = parse_actinia_jobs(resp)
                return make_response(jsonify(jobs), 200)
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
            else:
                log.error("ERROR: Internal Server Error")
                log.debug(f"actinia response: {getattr(resp, 'text', '')}")
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
