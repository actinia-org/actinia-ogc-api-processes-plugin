#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Process List class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response
from flask_restful_swagger_2 import Resource, swagger
from requests.exceptions import ConnectionError  # noqa: A004

from actinia_ogc_api_processes_plugin.apidocs import processlist

from actinia_ogc_api_processes_plugin.core.processlist import get_modules
from actinia_ogc_api_processes_plugin.model.response_models import (
    SimpleStatusCodeResponseModel,
)


class ProcessList(Resource):
    """ProcessList handling."""

    def __init__(self) -> None:
        """ProcessList class initialisation."""
        self.msg = (
            "TODO"
        )

    @swagger.doc(processlist.describe_processlist_get_docs)
    def get(self):
        """ProcessList get method.

        Returns process list with process identifiers
        and link to process descriptions.
        """
        get_modules()

    def post(self) -> SimpleStatusCodeResponseModel:
        """ProcessList post method: not allowed response."""
        res = jsonify(
        SimpleStatusCodeResponseModel(
                status=405,
                message="Method Not Allowed",
            ),
        )
        return make_response(res, 405)

