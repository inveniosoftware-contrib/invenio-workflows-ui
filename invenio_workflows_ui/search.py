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

from invenio_search import current_search_client, Query

from .utils import obj_or_import_string


def default_query_factory(search, query_string, page, size):
    """Create default ES query based on query-string pattern."""
    query = Query()
    if query_string.strip():
        query.body['query'] = dict(
            query_string=dict(
                query=query_string,
                allow_leading_wildcard=False,
            )
        )
    # only return ids
    query.body['fields'] = []
    query = query[(page - 1) * size:page * size]
    return query


def default_sorter_factory(search, query, sort_key):
    """Add sorting parameters to query body."""
    if sort_key.endswith("_desc"):
        order = "desc"
        sort_key = sort_key[:-5]
    else:
        order = "asc"

    if not sort_key:
        sort_key = "modified"

    sorting = {
        sort_key: {
            "order": order
        }
    }
    return query.sort(*[sorting])


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
        return WorkflowUISearch(**app.config['WORKFLOWS_UI_SEARCH'])

    def search(self, query_string, size=25, page=1, sort_key="_workflow.modified"):
        """Return search results for query."""
        query = self.query_factory(self, query_string, page, size)
        query = self.sorter_factory(self, query, sort_key)

        search_result = current_search_client.search(
            index=self.search_index,
            doc_type=self.search_type,
            body=query.body,
            version=True,
        )
        return search_result, int(search_result['hits']['total'])
