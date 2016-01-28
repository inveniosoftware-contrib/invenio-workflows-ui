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

Holding Pen is a web interface overlay for all DbWorkflowObject's.

This area is targeted to catalogers and administrators for inspecting
and reacting to workflows executions. More importantly, allowing users to deal
with halted workflows.

For example, accepting submissions or other tasks.
"""

from __future__ import absolute_import, print_function

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

from flask_login import login_required

from invenio_workflows.api import continue_oid_delayed, start_delayed
from invenio_workflows.models import DbWorkflowObject, ObjectStatus, Workflow

from .proxies import actions

from .search import get_holdingpen_objects
from .utils import (
    get_rows,
    get_data_types,
    get_rendered_task_results,
    get_previous_next_objects,
    alert_response_wrapper
)



#
#
# from ..acl import viewholdingpen


blueprint = Blueprint(
    'invenio_workflows_ui',
    __name__,
    url_prefix="/holdingpen",
    template_folder='templates',
    static_folder='static',
)

# FIXME Replace or move to another place
from math import ceil
class Pagination(object):
    """Helps with rendering pagination list."""

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        """Returns number of pages."""
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        """Returns true if it has previous page."""
        return self.page > 1

    @property
    def has_next(self):
        """Returns true if it has next page."""
        return self.page < self.pages

    def iter_pages(self, left_edge=1, left_current=1,
                   right_current=3, right_edge=1):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

# TODO Could we avoid having Yet Another Mapping?
HOLDINGPEN_WORKFLOW_STATES = {
    DbWorkflowObject.known_statuses.HALTED: {
        'message': _(DbWorkflowObject.known_statuses.HALTED.label),
        'class': 'danger'
    },
    DbWorkflowObject.known_statuses.WAITING: {
        'message': _(DbWorkflowObject.known_statuses.WAITING.label),
        'class': 'warning'
    },
    DbWorkflowObject.known_statuses.ERROR: {
        'message': _(DbWorkflowObject.known_statuses.ERROR.label),
        'class': 'danger'
    },
    DbWorkflowObject.known_statuses.COMPLETED: {
        'message': _(DbWorkflowObject.known_statuses.COMPLETED.label),
        'class': 'success'
    },
    DbWorkflowObject.known_statuses.INITIAL: {
        'message': _(DbWorkflowObject.known_statuses.INITIAL.label),
        'class': 'info'
    },
    DbWorkflowObject.known_statuses.RUNNING: {
        'message': _(DbWorkflowObject.known_statuses.RUNNING.label),
        'class': 'warning'
    }
}


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
#@login_required
def index():
    """
    Display main interface of Holdingpen.

    Acts as a hub for catalogers (may be removed)
    """
    # TODO: Add user filtering
    error_state_total = get_holdingpen_objects(
       tags_list=[ObjectStatus.labels[ObjectStatus.ERROR.value]]
    )[1]
    halted_state_total = get_holdingpen_objects(
       tags_list=[ObjectStatus.labels[ObjectStatus.HALTED.value]]
   )[1]
    return render_template('invenio_workflows_ui/index.html',error_state_total=error_state_total,
                           halted_state_total=halted_state_total)


@blueprint.route('/load', methods=['GET', 'POST'])
#@login_required
#@permission_required(viewholdingpen.name)
def load(page=1, per_page=0, sort_key="modified"):
    """Load objects for the table."""
    tags = request.args.getlist("tags[]") or []  # empty to show all
    sort_key = request.args.get(
        'sort_key', session.get('holdingpen_sort_key', "modified")
    )
    page = max(page, 1)
    per_page = per_page or session.get('holdingpen_per_page') or 25

    current_app.logger.debug(tags)
    ids, total = get_holdingpen_objects(
        tags_list=tags, per_page=per_page, page=page, sort_key=sort_key
    )

    current_app.logger.debug("Total hits: {0}".format(ids))
    current_app.logger.debug(ids)

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
    session['holdingpen_current_ids'] = ids
    session['holdingpen_sort_key'] = sort_key
    session['holdingpen_per_page'] = per_page
    session['holdingpen_page'] = page
    session['holdingpen_tags'] = tags

    table_data["rows"] = get_rows(ids)
    table_data["rendered_rows"] = "".join(table_data["rows"])
    return jsonify(table_data)


@blueprint.route('/list', methods=['GET', ])
@blueprint.route('/list/', methods=['GET', ])
@blueprint.route('/list/<tags_slug>', methods=['GET', ])
#@login_required
#@permission_required(viewholdingpen.name)
def list_objects(tags_slug=None):
    """Display main table interface of Holdingpen."""
    tags = [tag for tag in tags_slug.split(' AND ')] if tags_slug \
        else session.get("holdingpen_tags",
                         ['version:"{0}"'.format(
                             ObjectStatus.labels[ObjectStatus.HALTED.value]
                         )])

    tags_to_print = [
        {"text": tag.replace('"', '\\"'), "value": tag.replace('"', '\\"')}
        for tag in tags if tag
    ]
    sort_key = request.args.get(
        'sort_key', session.get('holdingpen_sort_key', "modified")
    )
    page = request.args.get(
        'page', session.get('holdingpen_page', 1)
    )
    per_page = request.args.get(
        'per_page', session.get('holdingpen_per_page', 25)
    )
    return render_template(
        'invenio_workflows_ui/list.html',
        tags=json.dumps(tags_to_print),
        total=get_holdingpen_objects(
            tags_list=tags, per_page=per_page, page=page, sort_key=sort_key
        )[1],
        type_list=get_data_types(),
        per_page=session.get('holdingpen_per_page')
    )


@blueprint.route('/<int:objectid>', methods=['GET', 'POST'])
@blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
#@login_required
#@permission_required(viewholdingpen.name)
def details(objectid):
    """Display info about the object."""
    bwobject = DbWorkflowObject.query.get_or_404(objectid)

    # FIXME(jacquerie): to be removed in workflows >= 2.0
    bwobject.data = bwobject.get_data()
    bwobject.extra_data = bwobject.get_extra_data()

    previous_object, next_object = get_previous_next_objects(
        session.get("holdingpen_current_ids"),
        objectid
    )
    formatted_data = bwobject.get_formatted_data()
    action_name = bwobject.get_action()
    if action_name:
        action = actions[action_name]
        rendered_actions = action().render(bwobject)
    else:
        rendered_actions = {}

    results = get_rendered_task_results(bwobject)
    return render_template(
        'workflows/details.html',
        bwobject=bwobject,
        rendered_actions=rendered_actions,
        data_preview=formatted_data,
        workflow_name=bwobject.get_workflow_name() or "",
        task_results=results,
        previous_object=previous_object,
        next_object=next_object,
    )


@blueprint.route('/result/<int:object_id>/<path:filename>',
                 methods=['POST', 'GET'])
#@login_required
#@permission_required(viewholdingpen.name)
def get_file_from_task_result(object_id=None, filename=None):
    """Send the requested file to user from a workflow task result.

    Expects a certain file meta-data structure in task result:

    .. code-block:: python

        {
            "type": "Fulltext",
            "filename": "file.pdf",
            "full_path": "/path/to/file",
        }

    """
    bwobject = DbWorkflowObject.query.get_or_404(object_id)
    task_results = bwobject.get_tasks_results()
    if filename in task_results and task_results[filename]:
        fileinfo = task_results[filename][0].get("result", dict())
        directory, actual_filename = os.path.split(
            fileinfo.get("full_path", ""))
        return send_from_directory(directory, actual_filename)
    abort(404)


@blueprint.route('/file/<int:object_id>/<path:filename>',
                 methods=['POST', 'GET'])
#@login_required
#@permission_required(viewholdingpen.name)
def get_file_from_object(object_id=None, filename=None):
    """Send the requested file to user from a workflow object FFT value."""
    bwobject = DbWorkflowObject.query.get_or_404(object_id)
    data = bwobject.get_data()
    urls = data.get("fft.url", [])
    for url in urls:
        if os.path.basename(filename) == os.path.basename(url):
            directory, actual_filename = os.path.split(url)
            return send_from_directory(directory, actual_filename)
    # Return 404


@blueprint.route('/restart_record', methods=['GET', 'POST'])
#@login_required
#@permission_required(viewholdingpen.name)
@alert_response_wrapper
def restart_record(objectid=None, start_point='continue_next'):
    """Restart the initial object in its workflow."""
    bwobject = DbWorkflowObject.query.get_or_404(objectid)

    workflow = Workflow.query.filter(
        Workflow.uuid == bwobject.id_workflow).first()

    start_delayed(workflow.name, [bwobject.get_data()])
    return jsonify(dict(
        category="success",
        message=_("Object restarted successfully.")
    ))


@blueprint.route('/continue_record', methods=['GET', 'POST'])
#@login_required
#@permission_required(viewholdingpen.name)
#@alert_response_wrapper
def continue_record(objectid=None):
    """Continue workflow for current object."""
    continue_oid_delayed(oid=objectid, start_point='continue_next')
    return jsonify(dict(
        category="success",
        message=_("Object continued with next task successfully.")
    ))


#@login_required
#@permission_required(viewholdingpen.name)
@blueprint.route('/restart_record_prev/', methods=['GET', 'POST'])
@alert_response_wrapper
def restart_record_prev():
    """Restart the last task for current object."""
    objectid = request.form["objectid"]
    continue_oid_delayed(oid=objectid, start_point="restart_task")
    return jsonify(dict(
        category="success",
        message=_("Object restarted task successfully.")
    ))


@blueprint.route('/delete', methods=['GET', 'POST'])
#@login_required
#@permission_required(viewholdingpen.name)
#@alert_response_wrapper
def delete_from_db():
    """Delete the object from the db."""
    objectid = request.form["objectid"]
    DbWorkflowObject.delete(objectid)
    return jsonify(dict(
        category="success",
        message=_("Object deleted successfully.")
    ))


@blueprint.route('/delete_multi', methods=['GET', 'POST'])
#@login_required
#@permission_required(viewholdingpen.name)
@alert_response_wrapper
def delete_multi():
    """Delete list of objects from the db."""
    from .utils import parse_bwids
    bwolist = request.form["bwolist"]
    bwolist = parse_bwids(bwolist)
    for objectid in bwolist:
        delete_from_db(objectid)
    return jsonify(dict(
        category="success",
        message=_("Objects deleted successfully.")
    ))


@blueprint.route('/resolve', methods=['GET', 'POST'])
#@login_required
#@permission_required(viewholdingpen.name)
def resolve_action():
    """Resolve the action taken.

    Will call the resolve() function of the specific action.
    """
    objectids = request.values.getlist('objectids[]') or []
    ids_resolved = 0

    for objectid in objectids:
        bwobject = DbWorkflowObject.query.get_or_404(objectid)
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


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
#@login_required
#@permission_required(viewholdingpen.name)
def entry_data_preview():
    """Present the data in a human readble form or in xml code."""
    objectid = request.form["objectid"]
    of = request.form["of"]
    bwobject = DbWorkflowObject.query.get_or_404(objectid)
    if not bwobject:
        flash("No object found for %s" % (objectid,))
        return jsonify(data={})
    formatted_data = bwobject.get_formatted_data(of=of)
    return jsonify(data=formatted_data)
