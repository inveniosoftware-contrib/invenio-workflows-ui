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

"""Deposit actions."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import Blueprint, request, url_for

from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.decorators import require_content_types
from invenio_rest.errors import RESTException
from invenio_search import current_search_client
from invenio_workflows import WorkflowObject

from ..search import (
    WorkflowUISearch,
    default_query_factory,
    default_sorter_factory,
)
from ..utils import obj_or_import_string


def create_blueprint(config):
    """Create Invenio-Deposit-REST blueprint."""
    blueprint = Blueprint(
        'invenio_workflows_rest',
        __name__,
        url_prefix='',
    )

    workflow_object_serializers = config.get('workflow_object_serializers')
    search_serializers = config.get('search_serializers')
    default_media_type = config.get('default_media_type')
    search_index = config.get('search_index')
    max_result_window = config.get('max_result_window')

    query_factory = config.get('query_factory', default_query_factory)
    sorter_factory = config.get('sorter_factory', default_sorter_factory)

    workflow_object_serializers = {
        mime: obj_or_import_string(func)
        for mime, func in workflow_object_serializers.items()
    }
    search_serializers = {
        mime: obj_or_import_string(func)
        for mime, func in search_serializers.items()
    }

    list_view = WorkflowsListResource.as_view(
        WorkflowsListResource.view_name,
        search_serializers=search_serializers,
        workflow_object_serializers=workflow_object_serializers,
        default_media_type=default_media_type,
        search_index=search_index,
        query_factory=query_factory,
        sorter_factory=sorter_factory,
        max_result_window=max_result_window
    )
    list_route = config.get('list_route')

    item_view = WorkflowObjectResource.as_view(
        WorkflowObjectResource.view_name,
        serializers=workflow_object_serializers,
        default_media_type=default_media_type,
    )
    item_route = config.get('item_route')

    views = [
        dict(rule=list_route, view_func=list_view),
        dict(rule=item_route, view_func=item_view),
    ]

    for rule in views:
        blueprint.add_url_rule(**rule)

    return blueprint


def pass_workflow_object(f):
    """Decorator to retrieve workflow object."""
    @wraps(f)
    def inner(self, object_id, *args, **kwargs):
        workflow_object = WorkflowObject.query.get_or_404(object_id)
        return f(self, workflow_object=workflow_object, *args, **kwargs)
    return inner


class WorkflowsListResource(ContentNegotiatedMethodView):
    """Resource for records listing."""

    view_name = 'workflow_list'

    def __init__(self, read_permission_factory=None,
                 create_permission_factory=None,
                 workflow_object_serializers=None,
                 search_index=None, search_type=None,
                 record_loaders=None,
                 search_serializers=None, default_media_type=None,
                 max_result_window=None, facets_factory=None,
                 sorter_factory=None, query_factory=None,
                 item_links_factory=None, record_class=None, **kwargs):
        """Constructor."""
        super(WorkflowsListResource, self).__init__(
            method_serializers={
                'GET': search_serializers,
                'POST': workflow_object_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'POST': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs)
        self.searcher = WorkflowUISearch(
            sorter_factory=sorter_factory,
            query_factory=query_factory,
            search_index=search_index,
            search_type=search_type
        )
        self.max_result_window = max_result_window

    def get(self, **kwargs):
        """Search records.

        :returns: the search result containing hits and aggregations as
        returned by invenio-search.
        """
        page = request.values.get('page', 1, type=int)
        size = request.values.get('size', 10, type=int)
        if page * size >= self.max_result_window:
            raise RESTException("Too many results to show!")

        # Execute search
        urlkwargs, search_result = self.searcher.search(size=size, page=page)

        # Generate links for prev/next
        urlkwargs.update(
            size=size,
            q=request.values.get('q', ''),
            _external=True,
        )
        endpoint = '.{0}'.format(self.view_name)
        links = dict(self=url_for(endpoint, page=page, **urlkwargs))
        if page > 1:
            links['prev'] = url_for(endpoint, page=page-1, **urlkwargs)
        if size * page < int(search_result['hits']['total']) and \
                size * page < self.max_result_window:
            links['next'] = url_for(endpoint, page=page+1, **urlkwargs)

        return self.make_response(
            search_result=search_result,
            links=links,
        )

    def post(self, **kwargs):
        """Create a record.

        :returns: The created record.
        """
        if request.content_type not in self.loaders:
            abort(415)

        data = self.loaders[request.content_type]()
        if data is None:
            abort(400)

        try:
            # Create uuid for record
            record_uuid = uuid.uuid4()
            # Create persistent identifier
            pid = self.minter(record_uuid, data=data)
            # Create record
            record = self.record_class.create(data, id_=record_uuid)

            # Check permissions
            permission_factory = self.create_permission_factory
            if permission_factory:
                verify_record_permission(permission_factory, record)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception('Failed to create record.')
            abort(500)
        response = self.make_response(pid, record, 201,
                                      links_factory=self.item_links_factory)

        endpoint = '.{0}_item'.format(pid.pid_type)
        location = url_for(endpoint, pid_value=pid.pid_value, _external=True)
        response.headers.extend(dict(location=location))
        return response


class WorkflowObjectResource(ContentNegotiatedMethodView):
    """Resource for workflow items."""

    view_name = 'workflow_item'

    def __init__(self, resolver=None, read_permission_factory=None,
                 update_permission_factory=None,
                 delete_permission_factory=None, default_media_type=None,
                 links_factory=None,
                 loaders=None,
                 **kwargs):
        """Constructor."""
        super(WorkflowObjectResource, self).__init__(
            method_serializers={
                'DELETE': {'*/*': lambda *args: make_response(*args), },
            },
            default_method_media_type={
                'GET': default_media_type,
                'PUT': default_media_type,
                'DELETE': '*/*',
                'PATCH': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs)
        # self.resolver = resolver
        # self.read_permission_factory = read_permission_factory
        # self.update_permission_factory = update_permission_factory
        # self.delete_permission_factory = delete_permission_factory
        # self.links_factory = links_factory
        # self.loaders = loaders or current_records_rest.loaders

    @pass_workflow_object
    # @need_record_permission('read_permission_factory')
    def get(self, workflow_object, **kwargs):
        """Get a record.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The requested record.
        """
        return self.make_response(workflow_object)
