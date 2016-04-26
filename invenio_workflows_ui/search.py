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

from elasticsearch_dsl import Q


def default_query_factory(self, search, **kwargs):
    """Create default ES query based on query-string pattern."""
    if 'q' in kwargs:
        query_string = kwargs['q']
    else:
        query_string = request.values.get('q', '')
#    import ipdb; ipdb.set_trace()
    search = search.query(Q('query_string',
                            query=query_string,
                            allow_leading_wildcard=False))

    search_index = search._index[0]
    search, sortkwargs = default_sorter_factory(search, search_index, **kwargs)

    return (search, {'q': query_string})


def default_sorter_factory(search, index, **kwargs):
    """Add sorting parameters to query body."""
    if "sort" in kwargs:
        sort_key = kwargs["sort"]
    else:
        sort_key = request.args.get(
            "sort", "_workflow.modified", type=str
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
    return search.sort(*[sorting]), {"sort": sort_key}
