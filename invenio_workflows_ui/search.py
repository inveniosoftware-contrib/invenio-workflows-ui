# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Search functions for workflows UI interface."""

from __future__ import absolute_import, print_function

from flask import request

from invenio_search import current_search_client, Query

from .utils import obj_or_import_string


def default_query_factory(index, page, size, query_string=None):
    """Create default ES query based on query-string pattern."""
    if not query_string:
        query_string = request.values.get('q', '')

    query = Query()
    if query_string.strip():
        query.body['query'] = dict(
            query_string=dict(
                query=query_string,
                allow_leading_wildcard=False,
            )
        )
    query = query[(page-1)*size:page*size]
    return (query, {'q': query_string})


def default_sorter_factory(query, index, sort_key=None):
    """Add sorting parameters to query body."""
    sort_arg_name = "sort"
    if not sort_key:
        sort_key = request.args.get(
            sort_arg_name, "_workflow.modified", type=str
        )
    if sort_key.endswith("_desc"):
        order = "desc"
        sort_key = sort_key[:-5]
    else:
        order = "asc"

    if not sort_key:
        sort_key = "_workflow.modified"

    sorting = {
        sort_key: {
            "order": order
        }
    }
    return query.sort(*[sorting]), {sort_arg_name: sort_key}


class WorkflowUISearch(object):
    """Provides a search interface for workflow UI."""

    def __init__(self, search_index="workflows",
                 search_type=None,
                 query_factory=default_query_factory,
                 sorter_factory=default_sorter_factory):
        self.query_factory = obj_or_import_string(
            query_factory
        )
        self.sorter_factory = obj_or_import_string(
            sorter_factory
        )
        self.search_index = search_index
        self.search_type = search_type

    @classmethod
    def create(cls, app=None):
        """Create workflow ui search interface from ``WORKFLOWS_UI_SEARCH``."""
        if not app:
            from flask import current_app
            app = current_app
        search_index = app.config['WORKFLOWS_UI_REST_ENDPOINT'].get('search_index')
        return WorkflowUISearch(search_index=search_index)

    def search(self, size=25, page=1, query_string=None, sort_key=None):
        """Return search results for query."""
        # Arguments that must be added in prev/next links
        urlkwargs = dict()

        query, qs_kwargs = self.query_factory(
            self.search_index, page, size, query_string
        )
        urlkwargs.update(qs_kwargs)

        query, qs_kwargs = self.sorter_factory(
            query, self.search_index, sort_key
        )
        urlkwargs.update(qs_kwargs)

        search_result = current_search_client.search(
            index=self.search_index,
            doc_type=self.search_type,
            body=query.body,
            version=True,
        )
        return urlkwargs, search_result
