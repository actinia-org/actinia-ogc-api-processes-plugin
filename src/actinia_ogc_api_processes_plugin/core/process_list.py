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
from flask import jsonify, request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.resources.config import ACTINIA
from actinia_ogc_api_processes_plugin.resources.logging import log


def get_modules(limit: int | None = None):
    """Get all modules (for current user).

    All grass-modules and actinia-modules and format them
    """
    # Authentication for actinia
    auth = request.authorization
    kwargs = dict()
    kwargs["auth"] = HTTPBasicAuth(auth.username, auth.password)

    # Get all modules
    url_actinia_modules = f"{ACTINIA.processing_base_url}/actinia_modules"
    resp_actinia_modules = requests.get(
        url_actinia_modules,
        **kwargs,
    )
    url_grass_modules = f"{ACTINIA.processing_base_url}/grass_modules"
    resp_grass_modules = requests.get(
        url_grass_modules,
        **kwargs,
    )

    if (
        resp_grass_modules.status_code == 200
        and resp_actinia_modules.status_code == 200
    ):
        # from https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/schemas/processList.yaml
        # required: processes (array) + links (array)
        resp_format = dict()
        resp_format["processes"] = list()
        resp_format["links"] = list()
        # from https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/schemas/processSummary.yaml
        # and https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/schemas/descriptionType.yaml
        # required: id (string) + version (string)
        # optional: description (string) + keywords (array of strings)
        # -- actinia modules
        for el in json.loads(resp_actinia_modules.text)["processes"]:
            resp_format["processes"].append(
                {
                    "id": el["id"],
                    # TODO: when implemented in actinia module plugin:
                    # use version of actinia module template
                    "version": "1.0.0",
                    "description": el["description"],
                    "keywords": el["categories"],
                },
            )
        # -- grass modules
        url_version = f"{ACTINIA.processing_base_url}/version"
        resp_version = requests.get(url_version)
        grass_version = json.loads(resp_version.text)["grass_version"][
            "version"
        ]
        for el in json.loads(resp_grass_modules.text)["processes"]:
            resp_format["processes"].append(
                {
                    "id": el["id"],
                    # TODO: for non-official GRASS Addons:
                    # any better version than grass_version?
                    "version": grass_version,
                    "description": el["description"],
                    "keywords": el["categories"],
                },
            )
        if limit is not None:
            # TODO: use limit from actinia-module-plugin when implemented
            resp_format["processes"] = resp_format["processes"][:limit]
        # from https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/schemas/link.yaml
        # required: href (string)
        resp_format["links"].append(
            {
                "href": f"{request.url}?f=json",
                "rel": "self",
                "type": "application/json",
            },
            # Additional: a link to the response document
            # in every other media type supported by the service
            # (relation: alternate)
            # NOTE: until now only json supported
        )
        return (
            jsonify(resp_format),
            resp_grass_modules.status_code,
            resp_actinia_modules.status_code,
        )
    else:
        log.debug(
            f"grass_modules status code: {resp_grass_modules.status_code}",
        )
        log.debug(
            f"actinia_modules status code: {resp_actinia_modules.status_code}",
        )
        response_combined = {
            "grass_modules": resp_grass_modules.text,
            "actinia_modules": resp_actinia_modules.text,
        }
        log.debug(f"actinia response: {response_combined}")
        return (
            dict(),
            resp_grass_modules.status_code,
            resp_actinia_modules.status_code,
        )
