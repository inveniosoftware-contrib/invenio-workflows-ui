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

"""Search functions for Holding Pen interface."""

from flask import current_app

from invenio_base.globals import cfg
from invenio_base.helpers import unicodifier

from invenio_ext.es import es


class Query(object):
    """Search engine implemetation."""

    def __init__(self, query, **kwargs):
        """Initialize with search query and other arguments."""
        self.query = unicodifier(query)
        self.kwargs = kwargs

    def build(self, query):
        """Build engine query."""
        if not query:
            return {
                "match_all": []
            }
        return {
            "query_string": {
                "query": query
            }
        }

    def search(self, **kwargs):
        """Search records."""
        self.kwargs.update(kwargs)
        return Results(query=self.build(self.query), **self.kwargs)


class Results(object):
    """Search results wrapper."""

    def __init__(self, query, index=None, doc_type=None, **kwargs):
        """Create results object."""
        self.body = {
            'from': 0,
            'size': 10,
            'query': query,
        }
        self.body.update(kwargs)

        self.index = index
        self.doc_type = doc_type or 'record'

        self._results = None

    @property
    def recids(self):
        """Return list of recids for current query."""
        return [int(r['_id']) for r in self._search()['hits']['hits']]

    def _search(self):
        if self._results is None:
            self._results = es.search(
                index=self.index,
                doc_type=self.doc_type,
                body=self.body,
            )
        return self._results

    def records(self):
        """Return list of records for current query."""
        from invenio_records.api import Record
        return [Record(r['_source']) for r in self._search()['hits']['hits']]

    def __len__(self):
        """Return total number of hits."""
        return self._search()['hits']['total']


def search(query, per_page, page, sort=None):
    """Return a slice of matched workflow object IDs and total hits."""
    params = {
        "query": query,
        "index": cfg["WORKFLOWS_HOLDING_PEN_ES_PREFIX"] + "*",
        "doc_type": current_app.config.get("WORKFLOWS_HOLDING_PEN_DOC_TYPE"),
        "sort": sort or {},
        "size": min(per_page, 10000),
        "from": (page - 1) * min(per_page, 10000)
    }
    results = Query(**params)
    results = results.search()
    return results.recids, len(results)


def get_holdingpen_objects(tags_list=None,
                           sort_key="modified",
                           per_page=25,
                           page=1,
                           operator="AND"):
    """Get records for display in Holding Pen, return ids and total count."""
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
    return search(
        query=" {0} ".format(operator).join(tags_list),
        per_page=per_page,
        page=page,
        sort=sorting
    )
