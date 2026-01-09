#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2018-2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Response models
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Anika Weinmann, Carmen Tawalika"
__copyright__ = "Copyright 2018-2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


from typing import ClassVar

from flask_restful_swagger_2 import Schema


class SimpleStatusCodeResponseModel(Schema):
    """Simple response schema to inform about status."""

    type: str = "object"
    properties: ClassVar[dict] = {
        "status": {
            "type": "number",
            "description": "The status code of the request.",
        },
        "message": {
            "type": "string",
            "description": "A short message to describes the status",
        },
    }
    required: ClassVar[list[str]] = ["status", "message"]


simple_response_example = SimpleStatusCodeResponseModel(
    status=200,
    message="success",
)
SimpleStatusCodeResponseModel.example = simple_response_example


class StatusInfoResponseModel(Schema):
    """statusInfo schema from OGC API - Processes (part1)."""

    type: str = "object"
    properties: ClassVar[dict] = {
        "processID": {"type": "string"},
        "type": {"type": "string", "enum": ["process"]},
        "jobID": {"type": "string"},
        "status": {
            "type": "string",
            "enum": [
                "accepted",
                "running",
                "successful",
                "failed",
                "dismissed",
            ],
        },
        "message": {"type": "string"},
        "created": {"type": "string", "format": "date-time"},
        "started": {"type": "string", "format": "date-time"},
        "finished": {"type": "string", "format": "date-time"},
        "updated": {"type": "string", "format": "date-time"},
        "progress": {"type": "integer", "minimum": 0, "maximum": 100},
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "href": {"type": "string"},
                    "rel": {"type": "string"},
                    "type": {"type": "string"},
                    "hreflang": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["href"],
            },
        },
    }
    required: ClassVar[list[str]] = ["jobID", "status", "type"]


# attach examples
status_info_example = StatusInfoResponseModel(
    jobID="96ed4cb9-1290-4409-b034-c162759c10a1",
    status="successful",
    type="process",
    message="Processing successfully finished",
    processID="resource_id-96ed4cb9-1290-4409-b034-c162759c10a1",
    created="2026-01-06T11:02:14",
    updated="2026-01-06T11:02:49",
    finished="2026-01-06T11:02:49",
    progress=100,
    links=[
        {
            "href": (
                "http://example.com/jobs/"
                "96ed4cb9-1290-4409-b034-c162759c10a1"
            ),
            "rel": "self",
        },
    ],
)
StatusInfoResponseModel.example = status_info_example
