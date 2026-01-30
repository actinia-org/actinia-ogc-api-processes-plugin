#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

JobList endpoint implementation.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response, request
from flask_restful_swagger_2 import Resource, swagger
from requests.exceptions import ConnectionError as req_ConnectionError

from actinia_ogc_api_processes_plugin.apidocs import job_list
from actinia_ogc_api_processes_plugin.authentication import require_basic_auth
from actinia_ogc_api_processes_plugin.core.actinia_common import (
    map_status_reverse,
)
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
            # read optional type query parameter (array)
            job_types = request.args.getlist("type") or None
            if job_types and len(job_types) == 1 and "," in job_types[0]:
                job_types = [t for t in job_types[0].split(",") if t]

            # read optional processID query parameter (array)
            process_ids = request.args.getlist("processID") or None
            # support comma-separated single value
            if process_ids and len(process_ids) == 1 and "," in process_ids[0]:
                process_ids = [p for p in process_ids[0].split(",") if p]

            # read optional datetime query parameter (single value)
            datetime = request.args.get("datetime") or None

            # read optional status query parameter (array)
            job_status = request.args.getlist("status") or None
            if job_status and len(job_status) == 1 and "," in job_status[0]:
                job_status = [s for s in job_status[0].split(",") if s]

            # read optional duration filters (seconds)
            min_duration = request.args.get("minDuration") or None
            max_duration = request.args.get("maxDuration") or None

            # read optional limit parameter
            limit = request.args.get("limit") or 10000
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=400,
                        message="ERROR: Invalid limit parameter",
                    ),
                )
                return make_response(res, 400)
            if limit < 1 or limit > 10000:
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=400,
                        message="ERROR: Limit must be between 1 and 10000",
                    ),
                )
                return make_response(res, 400)

            # If a single status was requested and it maps to an actinia raw
            # type, forward the filter to actinia-core via the `type` query
            # parameter. If multiple job_status requested, request all jobs and
            # filter locally.
            actinia_type = None
            if job_status and len(job_status) == 1:
                actinia_type = map_status_reverse(job_status[0])

            resp = get_actinia_jobs(actinia_type=actinia_type, limit=limit)
            if resp.status_code == 200:
                jobs = parse_actinia_jobs(
                    resp,
                    job_types,
                    process_ids,
                    job_status,
                    datetime,
                    min_duration,
                    max_duration,
                )
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
