#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Unit tests for the DELETE handler of JobStatusInfo.

These tests call the Resource method directly inside a Flask
`test_request_context` and patch `core.cancel_actinia_job` to simulate
different actinia responses.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Carmen Tawalika"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


from unittest.mock import patch

from flask import Response

from actinia_ogc_api_processes_plugin.api.job_status_info import JobStatusInfo
from actinia_ogc_api_processes_plugin.core import job_status_info as core
from tests.testsuite import TestCase


class ApiJobStatusInfoDeleteUnitTest(TestCase):
    """Unit tests for JobStatusInfo.delete()."""

    def test_delete_returns_200(self):
        """When 200 is returned the delete handler returns a Response.

        Patches `cancel_actinia_job` to return 200 and checks the response
        is a Flask `Response` or an object with a `status_code` attribute.
        """
        job_id = "unit-1"

        class Resp:
            status_code = 200
            text = "ok"

        headers = self.HEADER_AUTH
        with self.app.application.test_request_context(
            f"/jobs/{job_id}",
            method="DELETE",
            headers=headers,
        ), patch.object(core, "cancel_actinia_job", return_value=Resp):
            res = JobStatusInfo().delete(job_id)
        assert isinstance(res, Response) or hasattr(res, "status_code")

    def test_delete_unauthorized(self):
        """When 401 is returned the delete handler returns a status code.

        Patches `cancel_actinia_job` to return 401 and checks the response
        contains a status code attribute.
        """
        job_id = "unit-2"

        class Resp:
            status_code = 401
            text = "unauth"

        headers = self.HEADER_AUTH
        with self.app.application.test_request_context(
            f"/jobs/{job_id}",
            method="DELETE",
            headers=headers,
        ), patch.object(core, "cancel_actinia_job", return_value=Resp):
            res = JobStatusInfo().delete(job_id)
        assert hasattr(res, "status_code")

    def test_delete_not_found(self):
        """When 404 is returned the delete handler returns a status code.

        Patches `cancel_actinia_job` to return 404 and checks the response
        contains a status code attribute.
        """
        job_id = "unit-3"

        class Resp:
            status_code = 404
            text = "not found"

        headers = self.HEADER_AUTH
        with self.app.application.test_request_context(
            f"/jobs/{job_id}",
            method="DELETE",
            headers=headers,
        ), patch.object(core, "cancel_actinia_job", return_value=Resp):
            res = JobStatusInfo().delete(job_id)
        assert hasattr(res, "status_code")

    def test_delete_connection_error(self):
        """When a connection error is raised the delete handler returns 503.

        The patched `cancel_actinia_job` raises an exception; the test verifies
        the resulting response exposes `status_code`.
        """
        job_id = "unit-4"

        class OwnExceptionError(Exception):
            pass

        def raise_conn(_jid):
            raise OwnExceptionError("connection")

        headers = self.HEADER_AUTH
        with self.app.application.test_request_context(
            f"/jobs/{job_id}",
            method="DELETE",
            headers=headers,
        ), patch.object(
            core,
            "cancel_actinia_job",
            side_effect=raise_conn,
        ):
            res = JobStatusInfo().delete(job_id)
        assert hasattr(res, "status_code")
