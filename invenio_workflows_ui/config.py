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


WORKFLOWS_UI_SEARCH = dict(
    search_index='workflows',
    search_type='record'
)

WORKFLOWS_UI_REST_ENDPOINTS = dict(
    workflows=dict(
        pid_type='wfui',
        pid_minter='workflow',
        pid_fetcher='workflow',
        search_index='workflows',
        search_type='record',
        record_class='invenio_workflows_ui.api:WorkflowUIRecord',
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/workflows/',
        item_route='/workflows/<pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
    ),
)
