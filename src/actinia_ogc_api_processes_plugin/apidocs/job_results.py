#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

API docs for JobResult endpoint.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)

describe_job_result_get_docs = {
    "tags": ["job_result"],
    "description": "Return job results.",
    "parameters": [
        {
            "name": "resultResponse",
            "in": "query",
            "required": False,
            "description": "Return job results with certain resultResponse.",
            "type": "string",
        },
        {
            "name": "transmissionMode",
            "in": "query",
            "required": False,
            "description": "Return job results with certain transmissionMode.",
            "type": "string",
        },
    ],
    "responses": {
        "200": {
            "description": "This response returns the jobs results.",
        },
        "204": {
            "description": (
                "This response returns the jobs results (raw + reference)."
            ),
        },
        "400": {
            "description": "Client error",
            "schema": SimpleStatusCodeResponseModel,
        },
        "401": {
            "description": "Unauthorized Access",
            "schema": SimpleStatusCodeResponseModel,
        },
        "405": {
            "description": "Not Allowed",
            "schema": SimpleStatusCodeResponseModel,
        },
        "422": {
            "description": "Unprocessable Content",
            "schema": SimpleStatusCodeResponseModel,
        },
        "500": {
            "description": "Internal Server Error",
            "schema": SimpleStatusCodeResponseModel,
        },
        "503": {
            "description": "Connection Error",
            "schema": SimpleStatusCodeResponseModel,
        },
    },
}
