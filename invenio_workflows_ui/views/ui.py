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

from functools import wraps

import json

import os

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

from flask_babelex import gettext as _
from flask.ext.celeryext import create_celery_app
from flask_login import login_required

from invenio_db import db

from invenio_workflows import (
    WorkflowObject,
    ObjectStatus,
    Workflow,
    resume,
)

from ..proxies import actions, searcher
from ..utils import (
    get_rows,
    get_data_types,
    get_previous_next_objects,
    Pagination
)

blueprint = Blueprint(
    'invenio_workflows_ui',
    __name__,
    url_prefix="/workflows",
    template_folder='../templates',
    static_folder='../static',
)


def alert_response_wrapper(func):
    """Wrap given function with wrapper to return JSON for alerts."""
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            current_app.logger.exception(error)
            return jsonify({
                "category": "danger",
                "message": "Error: {0}".format(error)
            })
    return inner


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """Display basic dashboard interface of Workflows UI."""
    error_state_total = searcher.search(ObjectStatus.labels[ObjectStatus.ERROR.value])[1]
    halted_state_total = searcher.search(ObjectStatus.labels[ObjectStatus.HALTED.value])[1]
    return render_template(current_app.config['WORKFLOWS_UI_INDEX_TEMPLATE'],
                           error_state_total=error_state_total,
                           halted_state_total=halted_state_total)


@blueprint.route('/load', methods=['GET', 'POST'])
@login_required
def load():
    """Load objects for the table."""
    tags = request.args.getlist("tags[]") or []  # empty to show all
    query_string = " AND ".join(tags)
    sort_key = request.args.get('sort_key', "_workflow.modified")
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)

    results, total = searcher.search(
        query_string, size=per_page, page=page, sort_key=sort_key
    )

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
    session['workflows_ui_tags'] = tags

    table_data["rows"] = get_rows(results)
    table_data["rendered_rows"] = "".join(table_data["rows"])
    return jsonify(table_data)


@blueprint.route('/list', methods=['GET', ])
@blueprint.route('/list/', methods=['GET', ])
@blueprint.route('/list/<tags_slug>', methods=['GET', ])
@login_required
def list_objects(tags_slug=None):
    """Display main table interface of workflows UI."""
    tags = [tag for tag in tags_slug.split(' AND ')] if tags_slug \
        else session.get("workflows_ui_tags",
                         ['status:"{0}"'.format(
                             ObjectStatus.labels[ObjectStatus.HALTED.value]
                         )])

    tags_to_print = [
        {"text": tag.replace('"', '\\"'), "value": tag.replace('"', '\\"')}
        for tag in tags if tag
    ]
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
        tags=json.dumps(tags_to_print),
        total=searcher.search(
            query_string=" AND ".join(tags), size=per_page, page=page, sort_key=sort_key
        )[1],
        type_list=get_data_types(),
        per_page=per_page
    )


@blueprint.route('/<int:objectid>', methods=['GET', 'POST'])
@blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
@login_required
def details(objectid):
    """Display info about the object."""
    bwobject = WorkflowObject.query.get_or_404(objectid)

    previous_object, next_object = get_previous_next_objects(
        session.get("workflows_ui_current_ids"),
        objectid
    )

    formatted_data = bwobject.get_formatted_data()
    action_name = bwobject.get_action()
    if action_name:
        action = actions[action_name]
        rendered_actions = action().render(bwobject)
    else:
        rendered_actions = {}

    return render_template(
        current_app.config['WORKFLOWS_UI_DETAILS_TEMPLATE'],
        bwobject=bwobject,
        rendered_actions=rendered_actions,
        data_preview=formatted_data,
        workflow_name=bwobject.get_workflow_name() or "",
        previous_object=previous_object,
        next_object=next_object,
    )


@login_required
@blueprint.route('/restart_record_prev/', methods=['GET', 'POST'])
@alert_response_wrapper
def restart_record_prev():
    """Restart the last task for current object."""
    objectid = request.form["objectid"]
    resume.delay(oid=objectid, restart_point="restart_task")
    return jsonify(dict(
        category="success",
        message=_("Object restarted task successfully.")
    ))


@blueprint.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_from_db():
    """Delete the object from the db."""
    objectid = request.form.get("objectid", None)
    if objectid:
        WorkflowObject.delete(objectid)
        db.session.commit()
        return jsonify(dict(
            category="success",
            message=_("Object deleted successfully.")
        ))
    else:
        return jsonify(dict(
            category="danger",
            message=_("Object doesn't exist.")
        ))


@blueprint.route('/resolve', methods=['GET', 'POST'])
@login_required
def resolve_action():
    """Resolve the action taken.

    Will call the resolve() function of the specific action.
    """
    # FIXME: TMP hack
    create_celery_app(current_app)

    objectids = request.values.getlist('objectids[]') or []
    ids_resolved = 0

    for objectid in objectids:
        bwobject = WorkflowObject.query.get_or_404(objectid)
        action_name = bwobject.get_action()

        if action_name:
            action_form = actions[action_name]
            res = action_form().resolve(bwobject)
            ids_resolved += 1

    if ids_resolved == 1:
        return jsonify(res)
    elif ids_resolved == 0:
        return jsonify({
            "message": "No records resolved!",
            "category": "danger"
        })
    else:
        return jsonify({
            "message": "{0} records resolved.".format(ids_resolved),
            "category": "info"
        })
