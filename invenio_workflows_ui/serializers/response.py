# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Serialization response factories.

Responsible for creating a HTTP response given the output of a serializer.
"""

from __future__ import absolute_import, print_function

from flask import current_app


def workflow_responsify(serializer, mimetype):
    """Create a Workflows-REST response serializer.

    :param serializer: Serializer function.
    :param mimetype: MIME type of response.
    """
    def view(workflow_object, code=200, headers=None):
        response = current_app.response_class(
            serializer.serialize(workflow_object),
            mimetype=mimetype)
        response.status_code = code

        if headers is not None:
            response.headers.extend(headers)
        return response
    return view


def action_responsify(serializer, mimetype):
    """Create a Workflows-REST action response serializer.

    :param serializer: Serializer function.
    :param mimetype: MIME type of response.
    """
    def view(data, code=200, headers=None):
        response = current_app.response_class(
            serializer.serialize_action(data),
            mimetype=mimetype)
        response.status_code = code

        if headers is not None:
            response.headers.extend(headers)
        return response
    return view


def file_responsify(serializer, mimetype):
    """Create a Workflows-REST file response serializer.

    :param serializer: Serializer function.
    :param mimetype: MIME type of response.
    """
    def view(data, code=200, headers=None):
        response = current_app.response_class(
            serializer.serialize_files(data),
            mimetype=mimetype)
        response.status_code = code

        if headers is not None:
            response.headers.extend(headers)
        return response
    return view


def search_responsify(serializer, mimetype):
    """Create a Workflows-REST search result response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    """
    def view(search_result, code=200, headers=None, links=None):
        response = current_app.response_class(
            serializer.serialize_search(search_result,
                                        links=links),
            mimetype=mimetype)
        response.status_code = code
        if headers is not None:
            response.headers.extend(headers)
        return response
    return view
