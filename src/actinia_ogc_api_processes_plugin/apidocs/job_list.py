#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

API docs for JobList endpoint.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)

describe_job_list_get_docs = {
    "tags": ["job_list"],
    "description": "List jobs for the requesting user.",
    "parameters": [
        {
            "name": "processID",
            "in": "query",
            "required": False,
            "description": "Filter jobs by process identifier(s).",
            "type": "array",
            "items": {"type": "string"},
        },
        {
            "name": "status",
            "in": "query",
            "required": False,
            "description": "Filter jobs by process status.",
            "type": "array",
            "items": {"type": "string"},
        },
        {
            "name": "minDuration",
            "in": "query",
            "required": False,
            "description": "Filter jobs by duration. Value is in seconds.",
            "type": "array",
            "items": {"type": "integer"},
        },
        {
            "name": "maxDuration",
            "in": "query",
            "required": False,
            "description": "Filter jobs by duration. Value is in seconds.",
            "type": "array",
            "items": {"type": "integer"},
        },
        {
            "name": "datetime",
            "in": "query",
            "required": False,
            "description": (
                "Filter jobs by creation time (`created` attribute). "
                "Value is either a single date-time or a time interval. "
                "Interval syntax: 'start/end', with open ends allowed using "
                "'..' or empty string. "
                "Examples: '2021-01-01T00:00:00Z', "
                "'2021-01-01T00:00:00Z/2021-01-02T00:00:00Z', "
                "'/../2021-01-02T00:00:00Z', '2021-01-01T00:00:00Z/..'"
            ),
            "type": "string",
        },
    ],
    "responses": {
        "200": {
            "description": "This response returns the jobs list.",
        },
        "401": {
            "description": "Unauthorized Access",
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
