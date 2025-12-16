#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2025 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Process List class
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2025 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"


from functools import wraps

from flask import jsonify, request


def require_basic_auth(realm: str = "Login Required"):
    """Apply decorator for HTTP Basic Auth.

    Compatible with flask_restful_swagger_2
    Set @require_basic_auth() for Resource methods
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            auth = request.authorization
            # NOTE: check auth (correct user + password) done within actinia
            if not auth:
                resp = jsonify({"message": "Authentication required"})
                resp.status_code = 401
                resp.headers["WWW-Authenticate"] = f"Basic realm='{realm}'"
                return resp
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
