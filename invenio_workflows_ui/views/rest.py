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

import os

from functools import partial, wraps

from flask import (
    abort,
    Blueprint,
    current_app,
    request,
    url_for,
    make_response,
)

from invenio_db import db
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.errors import RESTException
from invenio_search import RecordsSearch
from invenio_workflows import WorkflowObject

from ..api import WorkflowUIRecord

from ..search import (
    default_query_factory
)
from ..tasks import resolve_actions
from ..utils import obj_or_import_string


def create_blueprint(config, context_processors):
    """Create Invenio-Deposit-REST blueprint with all views."""
    blueprint = Blueprint(
        'invenio_workflows_rest',
        __name__,
        url_prefix='',
    )

    workflow_object_serializers = config.get('workflow_object_serializers')
    search_serializers = config.get('search_serializers')
    action_serializers = config.get('action_serializers')
    bulk_action_serializers = config.get('bulk_action_serializers')
    default_media_type = config.get('default_media_type')
    search_index = config.get('search_index')
    max_result_window = config.get('max_result_window')

    search_factory = config.get('search_factory', default_query_factory)

    search_factory = obj_or_import_string(search_factory)

    workflow_object_serializers = {
        mime: obj_or_import_string(func)
        for mime, func in workflow_object_serializers.items()
    }
    search_serializers = {
        mime: obj_or_import_string(func)
        for mime, func in search_serializers.items()
    }
    bulk_action_serializers = {
        mime: obj_or_import_string(func)
        for mime, func in bulk_action_serializers.items()
    }
    action_serializers = {
        mime: obj_or_import_string(func)
        for mime, func in action_serializers.items()
    }

    list_view = WorkflowsListResource.as_view(
        WorkflowsListResource.view_name,
        search_serializers=search_serializers,
        workflow_object_serializers=workflow_object_serializers,
        default_media_type=default_media_type,
        search_index=search_index,
        search_factory=search_factory,
        max_result_window=max_result_window
    )
    list_route = config.get('list_route')

    item_view = WorkflowObjectResource.as_view(
        WorkflowObjectResource.view_name,
        serializers=workflow_object_serializers,
        default_media_type=default_media_type,
    )
    item_route = config.get('item_route')

    actions_segment = "action/<any(resolve,restart,continue):action>"

    action_route = os.path.join(
        item_route,
        actions_segment
    )
    action_view = WorkflowActionResource.as_view(
        WorkflowActionResource.view_name,
        serializers=action_serializers,
        default_media_type=default_media_type,
    )

    bulk_action_route = os.path.join(
        list_route,
        actions_segment
    )
    bulk_action_view = WorkflowBulkActionResource.as_view(
        WorkflowBulkActionResource.view_name,
        serializers=bulk_action_serializers,
        default_media_type=default_media_type,
    )

    views = [
        dict(rule=list_route, view_func=list_view),
        dict(rule=item_route, view_func=item_view),
        dict(rule=action_route, view_func=action_view),
        dict(rule=bulk_action_route, view_func=bulk_action_view),
    ]

    for rule in views:
        blueprint.add_url_rule(**rule)

    for proc in context_processors:
        blueprint.context_processor(obj_or_import_string(proc))

    return blueprint


def pass_workflow_object(f):
    """Decorator to retrieve workflow object for use in views."""
    @wraps(f)
    def inner(self, object_id, *args, **kwargs):
        workflow_object = WorkflowObject.query.get_or_404(object_id)
        workflow_ui_object = WorkflowUIRecord.create(workflow_object)
        return f(self, workflow_ui_object=workflow_ui_object, *args, **kwargs)
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
                 max_result_window=None, search_factory=None,
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
        self.searcher = RecordsSearch(
            index=search_index,
            doc_type=search_type
        ).params(version=True)
        self.max_result_window = max_result_window
        self.search_factory = partial(search_factory, self)

    def get(self, **kwargs):
        """Search records.

        :returns: the search result containing hits and aggregations as
        returned by invenio-search.
        """
        page = request.values.get('page', 1, type=int)
        size = request.values.get('size', 10, type=int)
        if page * size >= self.max_result_window:
            raise RESTException("Too many results to show!")

        urlkwargs = dict()
        search = self.searcher[(page-1)*size:page*size]

        search, qs_kwargs = self.search_factory(search)

        urlkwargs.update(qs_kwargs)

        # Execute search
        search_result = search.execute()

        # Execute search
        # urlkwargs, search_result = self.searcher.search(size=size, page=page)

        # Generate links for prev/next
        urlkwargs.update(
            size=size,
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


    @pass_workflow_object
    # @need_record_permission('read_permission_factory')
    def get(self, workflow_ui_object, **kwargs):
        """Get a record.

        :param workflow_ui_object: WorkflowUIRecord object.
        :returns: The requested record.
        """
        return self.make_response(workflow_ui_object)

    @pass_workflow_object
    # @need_record_permission('delete_permission_factory')
    def delete(self, workflow_ui_object, **kwargs):
        """Delete a workflow object.

        :param workflow_ui_object: Workflow object.
        """
        try:
            db.session.delete(workflow_ui_object.model)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Failed to delete workflow object.')
            abort(500)
        return '', 204


class WorkflowActionResource(ContentNegotiatedMethodView):
    """"Workflow actions resource."""

    view_name = 'workflows_action'

    def __init__(self, serializers, *args, **kwargs):
        """Constructor."""
        super(WorkflowActionResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )

    @pass_workflow_object
    def post(self, workflow_ui_object, action, *args, **kwargs):
        from flask_login import current_user

        # Add data to kwargs (needed for potential async tasks)
        kwargs.update(request.form or {})
        kwargs['id_user'] = current_user.get_id()

        response = getattr(workflow_ui_object, action)(*args, **kwargs)
        db.session.commit()

        return self.make_response(dict(
            acknowledged=True,
            result=response,
        ), 200)


class WorkflowBulkActionResource(ContentNegotiatedMethodView):
    """"Workflow bulk-actions resource."""

    view_name = 'bulk_workflows_action'

    def __init__(self, serializers, *args, **kwargs):
        """Constructor."""
        super(WorkflowBulkActionResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )

    def post(self, object_ids, action, *args, **kwargs):
        """Handle deposit action."""
        from flask_login import current_user

        # Add data to kwargs (needed for potential async tasks)
        kwargs.update(request.form or {})
        kwargs['id_user'] = current_user.get_id()

        async_task = resolve_actions.delay(object_ids, action, *args, **kwargs)

        return self.make_response(dict(
            acknowledged=True,
            task_id=async_task.id,
        ))
