#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Hello World class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)

describe_process_list_get_docs = {
    # "summary" is taken from the description of the get method
    "tags": ["process_list"],
    "description": "Process identifiers, links to process descriptions.",
    "responses": {
        "200": {
            "description": (
                "This response returns the process identifiers "
                "and links to process description"
            ),
        },
        "401": {
            "description": (
                "This response returns an "
                "'Unauthorized Access' error message"
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
