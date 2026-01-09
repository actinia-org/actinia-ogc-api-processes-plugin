#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

API docs for JobStatusInfo endpoint.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
    StatusInfoResponseModel,
)

describe_job_status_info_get_docs = {
    "tags": ["job_status_info"],
    "description": "Retrieves the status information for a job.",
    "responses": {
        "200": {
            "description": "This response returns the job status information.",
            "schema": StatusInfoResponseModel,
        },
        "401": {
            "description": "Unauthorized Access",
            "schema": SimpleStatusCodeResponseModel,
        },
        "404": {
            "description": "Job not found",
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
