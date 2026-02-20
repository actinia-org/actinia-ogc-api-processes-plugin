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


from email.mime.multipart import MIMEMultipart

from flask import jsonify, make_response, request
from flask_restful_swagger_2 import Resource, swagger
from requests.exceptions import ConnectionError as req_ConnectionError

from actinia_ogc_api_processes_plugin.apidocs import job_results
from actinia_ogc_api_processes_plugin.authentication import require_basic_auth
from actinia_ogc_api_processes_plugin.core.job_results import (
    export_ref_to_header,
    export_ref_to_multipart,
    get_ref_value,
    get_results,
    stdout_to_multipart,
)
from actinia_ogc_api_processes_plugin.core.job_status_info import (
    get_job_status_info,
)
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)
from actinia_ogc_api_processes_plugin.resources.logging import log


class JobResults(Resource):
    """JobResults handling."""

    def __init__(self) -> None:
        """Initialise."""
        self.msg = "Return job results"

    @require_basic_auth()
    @swagger.doc(job_results.describe_job_result_get_docs)
    # ruff: noqa: PLR0911, PLR0912, PLR0915,
    def get(self, job_id):
        """Return job results for a given job id."""
        # ruff: noqa: PLR1702
        try:
            # -- read optional resultResponse parameter
            result_response = request.args.get("resultResponse") or "raw"
            # 7.11.2.4.  Response type:
            # "The default value, if the parameter is not specified is raw."
            if result_response and (
                result_response not in {"raw", "document"}
            ):
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=400,
                        message=(
                            "ERROR: resultResponse must be "
                            "'raw' or 'document'"
                        ),
                    ),
                )
                return make_response(res, 400)

            # -- read optional transmissionMode parameter
            transmission_mode = request.args.get("transmissionMode") or "mixed"
            # transmissionMode = mixed
            # - originally:
            #   if mutliple outputs with different transmission modes requested
            # - for actinia:
            #   automatically given if stdout (value) and
            #   exported results (reference) returned from
            # mixed allowed for all actinia results, thus choosen as default
            if transmission_mode and (
                transmission_mode not in {"value", "reference", "mixed"}
            ):
                res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=400,
                        message=(
                            "ERROR: transmissionMode must be "
                            "'value', 'reference' or 'mixed'"
                        ),
                    ),
                )
                return make_response(res, 400)

            # -- request job results
            status_code, status_info, resp = get_job_status_info(job_id)
            if status_code == 200:
                if status_info["status"] == "successful":
                    result_format, stdout_dict, export_out_dict = get_results(
                        resp,
                    )
                    # default status_code for most returns
                    status_code = 200
                    # -- Return results dependent on key-value of
                    #    response and transmissionMode
                    # Response Table 11 (7.11.4.):
                    # Not all of these combinations need to be implemented
                    # by a server conforming to this standard.
                    # Only the ones supported by server.
                    # -> for actinia: choose supported combinations different
                    #    for exported and stdout results
                    if result_response == "document":
                        # Note: for document the transmissionMode must not be
                        # filtered the correct formatting is already given by
                        # the results e.g. a tif can not be returned as raw
                        # binary in a json, so reference is used.
                        # If value desired, then it would need to be directly
                        # returned as e.g. base64 encoded (so already value)
                        # Especially for actinia result format already fixed:
                        # stdout -> value | export -> reference
                        # thus no need to filter for transmissionMode
                        return make_response(
                            jsonify(result_format),
                            status_code,
                        )
                    elif (
                        result_response == "raw"
                        and transmission_mode == "reference"
                    ):
                        # stdout result not supported as reference
                        if stdout_dict and not export_out_dict:
                            res = jsonify(
                                SimpleStatusCodeResponseModel(
                                    status=422,
                                    message=(
                                        "Format resultResponse=raw and "
                                        "transmissionMode=reference not "
                                        "supported for current job results. "
                                        "Use e.g. transmissionMode=value."
                                    ),
                                ),
                            )
                            return make_response(res, 422)
                        if stdout_dict and export_out_dict:
                            res = jsonify(
                                SimpleStatusCodeResponseModel(
                                    status=422,
                                    message=(
                                        "Format resultResponse=raw and "
                                        "transmissionMode=reference not "
                                        "supported for current job results. "
                                        "Use e.g. transmissionMode=mixed."
                                    ),
                                ),
                            )
                            return make_response(res, 422)
                        status_code = 204
                        return export_ref_to_header(result_format, status_code)
                    elif (
                        result_response == "raw"
                        and transmission_mode == "value"
                    ):
                        # -- single result
                        if len(result_format) == 1:
                            value = next(iter(result_format.values()))
                            if "href" in value:
                                return get_ref_value(
                                    value,
                                    status_code,
                                )
                            else:
                                return make_response(value, status_code)
                        # -- multiple results
                        if not stdout_dict and export_out_dict:
                            res = jsonify(
                                SimpleStatusCodeResponseModel(
                                    status=422,
                                    message=(
                                        "Format resultResponse=raw and "
                                        "transmissionMode=value not"
                                        "supported for current job results. "
                                        "Use e.g. transmissionMode=reference."
                                    ),
                                ),
                            )
                            return make_response(res, 422)
                        if stdout_dict and export_out_dict:
                            res = jsonify(
                                SimpleStatusCodeResponseModel(
                                    status=422,
                                    message=(
                                        "Format resultResponse=raw and "
                                        "transmissionMode=value not supported "
                                        "for current job results. "
                                        "Use e.g. transmissionMode=mixed."
                                    ),
                                ),
                            )
                            return make_response(res, 422)
                        # fallback: only stdout
                        multipart_message = MIMEMultipart("related")
                        if stdout_dict:
                            stdout_to_multipart(stdout_dict, multipart_message)

                        response = make_response(
                            multipart_message.as_string(),
                            status_code,
                        )
                        response.headers["Content-Type"] = "multipart/related"
                        return response
                    elif (
                        result_response == "raw"
                        and transmission_mode == "mixed"
                    ):
                        # Note: mixed is default, and also valid if only export
                        # or only stdout results returned
                        multipart_message = MIMEMultipart("related")
                        if export_out_dict:
                            export_ref_to_multipart(
                                result_format,
                                multipart_message,
                            )
                        if stdout_dict:
                            stdout_to_multipart(stdout_dict, multipart_message)

                        response = make_response(
                            multipart_message.as_string(),
                            status_code,
                        )
                        response.headers["Content-Type"] = "multipart/related"
                        return response
                elif status_info["status"] == "failed":
                    # return code from actinia,
                    # see also get_job_status_info() from core.job_status_info
                    failure_status_code = 400
                    # todo: use valid 'type' following
                    # OpenAPI 3.0 schema exception.yaml (RFC7807)
                    res = jsonify(
                        {
                            "type": "AsyncProcessError",
                            "title": "Job failed",
                            "status": failure_status_code,
                            "detail": (
                                f"Job '{job_id}' failed: "
                                f"{status_info['message']}"
                            ),
                            # "instance":
                            # TODO -> full actinia log url
                            # see also within core.job_results.get_results()
                            # here or/and within job_status_info?
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
