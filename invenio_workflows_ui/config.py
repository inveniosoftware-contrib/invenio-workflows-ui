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

"""Config variables for workflows module."""

WORKFLOWS_HOLDING_PEN_CACHE_TIMEOUT = 2629743  # one month
"""Determines the timeout when caching formatted Holding Pen rows."""

WORKFLOWS_HOLDING_PEN_DEFAULT_OUTPUT_FORMAT = "hd"
"""The default timeout when formatting Holding Pen detailed pages."""

WORKFLOWS_SNAPSHOTS_ENABLED = False
"""Enable to create an copy of each workflow object with initial data."""

WORKFLOWS_DATA_PROCESSORS = {
    'json': 'json.load',
    'marcxml': 'invenio_workflows.manage:split_marcxml',
}

WORKFLOWS_HOLDING_PEN_DOC_TYPE = "record"
"""The name of the Elasticsearch doc_type to use for Holding Pen records."""

WORKFLOWS_HOLDING_PEN_ES_PREFIX = "holdingpen-"
"""The prefix name of the Elasticsearch indices to use for Holding Pen.
For each record index, an equivalent is created for Holding Pen."""


WORKFLOWS_HOLDING_PEN_ES_PROPERTIES = {
    "global_fulltext": {
        "type": "string",
        "analyzer": "basic_analyzer"
    },
    "global_default": {
        "type": "string",
        "analyzer": "basic_analyzer"
    },
    "_collections": {
        "type": "string",
        "index": "not_analyzed"
    },
    "status": {
        "type": "string",
        "index": "not_analyzed"
    },
    "version": {
        "type": "string",
        "index": "not_analyzed"
    },
    "type": {
        "type": "string",
        "index": "not_analyzed"
    },
    "created": {
        "type": "date"
    },
    "modified": {
        "type": "date"
    },
    "uri": {
        "type": "string",
        "index": "not_analyzed"
    },
    "id_workflow": {
        "type": "string",
        "index": "not_analyzed"
    },
    "id_user": {
        "type": "integer",
        "index": "not_analyzed"
    },
    "id_parent": {
        "type": "integer",
        "index": "not_analyzed"
    },
    "workflow": {
        "type": "string",
        "index": "not_analyzed"
    }
}
"""The default properties that should be added to the Holding Pen index
mappings."""
