#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

API docs for landing page
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Anika Weinmann"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


describe_landing_page_get_docs = {
    # "summary" is taken from the description of the get method
    "tags": ["landing_page"],
    "description": "Process identifiers, links to process descriptions.",
    "responses": {
        "200": {
            "description": (
                "This response returns the landing page."
            ),
        },
    },
}
