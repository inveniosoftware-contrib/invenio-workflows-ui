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

"""UI layer for invenio-workflows.

workflows UI is a web interface overlay for all WorkflowObject's.

This area is targeted to catalogers and administrators for inspecting
and reacting to workflows executions. More importantly, allowing users to deal
with halted workflows.

For example, accepting submissions or other tasks.
"""

from __future__ import absolute_import, print_function

import json

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    render_template,
    request,
    send_from_directory,
    session,
    current_app
)

from flask_login import login_required


from invenio_workflows import (
    WorkflowObject,
    ObjectStatus,
)

from ..proxies import actions, searcher
from ..utils import (
    get_rows,
    get_data_types,
    get_previous_next_objects,
    Pagination
)


def create_blueprint(endpoint):
    """Create UI blueprint for invenio-workflows-ui."""

    blueprint = Blueprint(
        'invenio_workflows_ui',
        __name__,
        url_prefix=endpoint,
        template_folder='../templates',
        static_folder='../static',
    )

    @blueprint.route('/', methods=['GET', 'POST'])
    @blueprint.route('/index', methods=['GET', 'POST'])
    @login_required
    def index():
        """Display basic dashboard interface of Workflows UI."""
        q = '_workflow.status:"{0}"'
        error_state_total = searcher.search(
            query_string=q.format(ObjectStatus.labels[ObjectStatus.ERROR.value])
        )[1]['hits']['total']
        halted_state_total = searcher.search(
            query_string=q.format(ObjectStatus.labels[ObjectStatus.HALTED.value])
        )[1]['hits']['total']
        return render_template(current_app.config['WORKFLOWS_UI_INDEX_TEMPLATE'],
                               error_state_total=error_state_total,
                               halted_state_total=halted_state_total)


    @blueprint.route('/load', methods=['GET', 'POST'])
    @login_required
    def load():
        """Load objects for the table."""
        search = request.args.get("search") or ""  # empty to show all
        sort_key = request.args.get('sort_key', "_workflow.modified")
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)

        __, results = searcher.search(
            query_string=search, size=per_page, page=page, sort_key=sort_key
        )
        total = int(results['hits']['total'])
        current_app.logger.debug("Total hits: {0}".format(total))
        pagination = Pagination(page, per_page, total)

        # Make sure requested page is within limits.
        if pagination.page > pagination.pages:
            pagination.page = pagination.pages

        pages_iteration = []
        for iter_page in pagination.iter_pages():
            res = {"page": iter_page}
            if iter_page == pagination.page:
                res["active"] = True
            else:
                res["active"] = False
            pages_iteration.append(res)

        table_data = {
            'rows': [],
            'pagination': {
                "page": pagination.page,
                "pages": pagination.pages,
                "iter_pages": pages_iteration,
                "per_page": pagination.per_page,
                "total_count": pagination.total_count
            }
        }

        # Add current ids in table for use by previous/next
        session['workflows_ui_sort_key'] = sort_key
        session['workflows_ui_per_page'] = per_page
        session['workflows_ui_page'] = page
        session['workflows_ui_search'] = search

        table_data["rows"] = get_rows(results)
        table_data["rendered_rows"] = "".join(table_data["rows"])
        return jsonify(table_data)


    @blueprint.route('/list', methods=['GET', ])
    @blueprint.route('/list/', methods=['GET', ])
    @blueprint.route('/list/<search_value>', methods=['GET', ])
    @login_required
    def list_objects(search_value=None):
        """Display main table interface of workflows UI."""
        search_value = search_value or session.get(
            "workflows_ui_search",
            '_workflow.status:"{0}"'.format(
                ObjectStatus.labels[ObjectStatus.HALTED.value]
            )
        )
        sort_key = request.args.get(
            'sort_key', "_workflow.modified"
        )
        page = request.args.get(
            'page', session.get('workflows_ui_page', 1)
        )
        per_page = request.args.get(
            'per_page', session.get('workflows_ui_per_page', 25)
        )
        return render_template(
            current_app.config['WORKFLOWS_UI_LIST_TEMPLATE'],
            search=search_value,
            total=searcher.search(
                query_string=search_value, size=per_page, page=page, sort_key=sort_key
            )[1]['hits']['total'],
            type_list=get_data_types(),
            per_page=per_page
        )


    @blueprint.route('/<int:objectid>', methods=['GET', 'POST'])
    @blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
    @login_required
    def details(objectid):
        """Display info about the object."""
        workflow_object = WorkflowObject.query.get_or_404(objectid)

        previous_object_id, next_object_id = get_previous_next_objects(
            session.get("workflows_ui_current_ids"),
            objectid
        )

        formatted_data = workflow_object.get_formatted_data()
        action_name = workflow_object.get_action()
        if action_name:
            action = actions[action_name]
            rendered_actions = action().render(workflow_object)
        else:
            rendered_actions = {}

        return render_template(
            current_app.config['WORKFLOWS_UI_DETAILS_TEMPLATE'],
            workflow_object=workflow_object,
            rendered_actions=rendered_actions,
            data_preview=formatted_data,
            workflow_name=workflow_object.get_workflow_name() or "",
            previous_object_id=previous_object_id,
            next_object_id=next_object_id,
        )

    return blueprint
