# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Config variables for workflows UI module."""

from __future__ import absolute_import, print_function

from invenio_workflows_ui.search import terms_filter


WORKFLOWS_UI_URL = "/workflows"
WORKFLOWS_UI_API_URL = "/api/workflows/"
WORKFLOWS_UI_API_CLASS = "invenio_workflows_ui.api:WorkflowUIRecord"

WORKFLOWS_UI_TEMPLATE_CONTEXT_PROCESSORS = []
WORKFLOWS_UI_REST_ENDPOINT = dict(
    workflow_object_serializers={
        'application/json': ('invenio_workflows_ui.serializers'
                             ':json_serializer'),
    },
    search_serializers={
        'application/json': ('invenio_workflows_ui.serializers'
                             ':json_search_serializer'),
    },
    action_serializers={
        'application/json': ('invenio_workflows_ui.serializers'
                             ':json_action_serializer'),
    },
    bulk_action_serializers={
        'application/json': ('invenio_workflows_ui.serializers'
                             ':json_action_serializer'),
    },
    file_serializers={
        'application/json': ('invenio_workflows_ui.serializers'
                             ':json_file_serializer'),
    },
    list_route='/workflows/',
    item_route='/workflows/<object_id>',
    file_list_route='/workflows/<object_id>/files',
    file_item_route='/workflows/<object_id>/files/<path:key>',
    search_index="workflows",
    default_media_type='application/json',
    max_result_window=10000,
)

WORKFLOWS_UI_DATA_TYPES = dict(
    workflow=dict(
        search_index='workflows',
        search_type='record',
    ),
)

WORKFLOWS_UI_REST_FACETS = {
    "workflows": {
        "filters": {
            "status": terms_filter('_workflow.status'),
            "data_type": terms_filter('_workflow.data_type'),
            "workflow_name": terms_filter('_workflow.workflow_name'),
        },
        "aggs": {
            "status": {
                "terms": {
                    "field": "_workflow.status",
                    "size": 20
                }
            },
            "data_type": {
                "terms": {
                    "field": "_workflow.data_type",
                    "size": 20
                }
            },
            "workflow_name": {
                "terms": {
                    "field": "_workflow.workflow_name",
                    "size": 20
                }
            },
        }
    }
}

WORKFLOWS_UI_REST_SORT_OPTIONS = {
    "workflows": {
        "bestmatch": {
            "title": 'Best match',
            "fields": ['_score'],
            "default_order": 'desc',
            "order": 1,
        },
        "mostrecent": {
            "title": 'Most recent',
            "fields": ['_workflow.modified'],
            "default_order": 'desc',
            "order": 2,
        },
    },
}

WORKFLOWS_UI_REST_DEFAULT_SORT = {
    "workflows": {
        "query": "-bestmatch",
        "noquery": "-mostrecent"
    }
}


WORKFLOWS_UI_CACHE_PREFIX = "WorkflowsUI::"
WORKFLOWS_UI_LIST_TEMPLATE = "invenio_workflows_ui/list.html"
WORKFLOWS_UI_DETAILS_TEMPLATE = "invenio_workflows_ui/details.html"
WORKFLOWS_UI_INDEX_TEMPLATE = "invenio_workflows_ui/index.html"

WORKFLOWS_UI_JSTEMPLATE_RESULTS = (
    "templates/invenio_workflows_ui/results.html"
)
WORKFLOWS_UI_JSTEMPLATE_COUNT = (
    "templates/invenio_search_ui/count.html"
)
WORKFLOWS_UI_JSTEMPLATE_PAGINATION = (
    "templates/invenio_search_ui/pagination.html"
)
WORKFLOWS_UI_JSTEMPLATE_SELECT_BOX = (
    "templates/invenio_search_ui/selectbox.html"
)
WORKFLOWS_UI_JSTEMPLATE_SORT_ORDER = (
    "templates/invenio_search_ui/togglebutton.html"
)
WORKFLOWS_UI_JSTEMPLATE_ERROR = "templates/invenio_search_ui/error.html"
WORKFLOWS_UI_JSTEMPLATE_LOADING = "templates/invenio_search_ui/loading.html"
WORKFLOWS_UI_JSTEMPLATE_FACETS = (
    "node_modules/invenio-search-js/dist/templates/facets.html"
)
