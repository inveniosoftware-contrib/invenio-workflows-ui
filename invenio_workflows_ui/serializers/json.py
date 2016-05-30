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

"""Marshmallow based JSON serializer for records."""

from __future__ import absolute_import, print_function

from flask import current_app, json, request


class JSONSerializer(object):
    """JSON serializer for workflow object.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    @staticmethod
    def _format_args():
        """Get JSON dump indentation and separates."""
        if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and \
                not request.is_xhr:
            return dict(
                indent=2,
                separators=(', ', ': '),
            )
        else:
            return dict(
                indent=None,
                separators=(',', ':'),
            )

    def serialize(self, workflow_ui_object):
        """Serialize a single workflow object.

        :param workflow_ui_object: workflow record instance.
        """
        return json.dumps(workflow_ui_object.dumps(), **self._format_args())

    def serialize_action(self, data):
        """Serialize an action response.

        :param workflow_ui_object: workflow record instance.
        """
        return json.dumps(dict(data), **self._format_args())

    def serialize_files(self, data):
        """Serialize files for a workflow object.

        :param data: some data object to serialize
        """
        from invenio_workflows.models import WorkflowFilesIterator
        if isinstance(data, WorkflowFilesIterator):
            return json.dumps([
                file_obj.dumps() for file_obj in data
            ], **self._format_args())
        else:
            return json.dumps(data.dumps(), **self._format_args())

    def serialize_search(self, search_result, links=None):
        """Serialize a search result.

        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        return json.dumps(dict(
            hits=dict(
                hits=search_result['hits']['hits'],
                total=search_result['hits']['total'],
            ),
            links=links or {},
            aggregations=search_result.get('aggregations', dict()),
        ), **self._format_args())
