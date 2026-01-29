#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Process Execution class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika, Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)

describe_process_execution_post_docs = {
    # "summary" is taken from the description of the get method
    "tags": ["process_execution"],
    "description": "Executes a process.",
    "responses": {
        "201": {
            "description": "This response returns the status info of the "
            "successfully started process.",
        },
        "401": {
            "description": (
                "This response returns an "
                "'Unauthorized Access' error message"
            ),
            "schema": SimpleStatusCodeResponseModel,
        },
        "404": {
            "description": (
                "This response returns an 'No such process' error message"
            ),
            "schema": SimpleStatusCodeResponseModel,
        },
        "500": {
            "description": (
                "This response returns an "
                "'Internal Server Error' error message"
            ),
            "schema": SimpleStatusCodeResponseModel,
        },
        "503": {
            "description": (
                "This response returns an 'Connection Error' error message"
            ),
            "schema": SimpleStatusCodeResponseModel,
        },
    },
}
