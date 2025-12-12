#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Example core functionality
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


import json

import requests
from flask import request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.resources.config import ACTINIA


def get_modules(event) -> str:
    """Get all modules (for current user): grass- and actinia-modules."""

    url = f"{ACTINIA.processing_base_url}/modules"

    postkwargs = dict()
    postkwargs["auth"] = HTTPBasicAuth(ACTINIA.user, ACTINIA.password)

    # TODO: post or get? eig get, aber muss authentication mit posten
    resp = requests.post(
        url,
        **postkwargs,
    )

    # Part of resp: -> TODO: UPDATE
    # 'message' = 'Resource accepted'
    # 'queue' = 'job_queue_resource_id-cddae7bb-b4fa-4249-aec4-2a646946ff36'
    # 'resource_id' = 'resource_id-cddae7bb-b4fa-4249-aec4-2a646946ff36'
    # 'status' = 'accepted'
    # 'urls' = {
    #    'resources': [],
    #    'status':
    #    'http://actinia-dev:8088/api/v3/resources/actinia-gdi/
    #    resource_id-cddae7bb-b4fa-4249-aec4-2a646946ff36'}

    return json.loads(resp.text)
