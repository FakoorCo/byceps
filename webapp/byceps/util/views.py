# -*- coding: utf-8 -*-

"""
byceps.util.views
~~~~~~~~~~~~~~~~~

View utilities.

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from functools import wraps

from flask import jsonify, redirect, Response, url_for


def jsonified(f):
    """Send the data returned by the decorated function as JSON."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        data = f(*args, **kwargs)
        return jsonify(data)
    return wrapper


def respond_created(f):
    """Send a ``201 Created`` response.

    The decorated callable is expected to return the URL of the newly created
    resource.  That URL is then added to the response as ``Location:`` header.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        url = f(*args, **kwargs)
        return Response(status=201, headers=[('Location', url)])
    return wrapper


def respond_no_content(f):
    """Send a ``204 No Content`` response.

    Optionally, a list of header may be returned by the decorated callable.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        headers = f(*args, **kwargs)
        return Response(status=204, headers=headers)
    return wrapper


def redirect_to(endpoint, **values):
    return redirect(url_for(endpoint, **values))
