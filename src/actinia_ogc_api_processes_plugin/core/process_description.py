#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Example core functionality
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import requests
from flask import request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.resources.config import ACTINIA


def get_module_description(process_id):
    """Get modules description for given process_id."""
    # Authentication for actinia
    auth = request.authorization
    kwargs = dict()
    kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    # Get module description
    url_module_description = (
        f"{ACTINIA.processing_base_url}/modules/{process_id}"
    )
    # TODO: adjust format following "OGC Process Description":
    # https://docs.ogc.org/is/18-062r2/18-062r2.html#ogc_process_description

    return requests.get(
        url_module_description,
        **kwargs,
    )
