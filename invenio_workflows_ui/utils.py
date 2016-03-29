# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015, 2016 CERN.
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

"""Various utility functions for use across the workflows module."""

from flask import current_app, jsonify, render_template

import msgpack

from math import ceil

from six import text_type

from invenio_workflows.models import WorkflowObject

from .proxies import current_workflows_ui



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


def get_formatted_holdingpen_object(bwo, date_format='%Y-%m-%d %H:%M:%S.%f'):
    """Return the formatted output, from cache if available."""
    results = current_workflows_ui.get("row::{0}".format(bwo.id))
    if results:
        results = msgpack.loads(results)
        if results["date"] == bwo.modified.strftime(date_format):
            return results
    results = generate_formatted_holdingpen_object(bwo)
    if results:
        current_workflows_ui.set(
            "row::{0}".format(bwo.id),
            msgpack.dumps(results)
        )
    return results


def generate_formatted_holdingpen_object(
        bwo, date_format='%Y-%m-%d %H:%M:%S.%f'):
    """Generate a dict with formatted column data from Holding Pen object."""
    from invenio_workflows import workflows

    from .definitions import WorkflowBase

    workflows_name = bwo.get_workflow_name()

    if workflows_name and workflows_name in workflows and \
       hasattr(workflows[workflows_name], 'get_description'):
        workflow_definition = workflows[workflows_name]
    else:
        workflow_definition = WorkflowBase

    action_name = bwo.get_action() or ""
    action = current_workflows_ui.actions.get(action_name, None)
    mini_action = getattr(action, "render_mini", "")
    if mini_action:
        mini_action = action().render_mini(bwo)

    results = {
        "name": workflows_name,
        "description": workflow_definition.get_description(bwo),
        "title": workflow_definition.get_title(bwo),
        "date": bwo.modified.strftime(date_format),
        "additional": workflow_definition.get_additional(bwo),
        "action": mini_action,
        "sort_data": workflow_definition.get_sort_data(bwo)
    }
    return results


def get_data_types():
    """Return a list of distinct data types from WorkflowObject."""
    return [
        t[0] for t in WorkflowObject.query.with_entities(
            WorkflowObject.data_type
        ).distinct(
            WorkflowObject.data_type
        )
    ]


def get_action_list(object_list):
    """Return a dict of action names mapped to halted objects.

    Get a dictionary mapping from action name to number of Pending
    actions (i.e. halted objects). Used in the holdingpen.index page.
    """
    action_dict = {}
    found_actions = []

    # First get a list of all to count up later
    for bwo in object_list:
        action_name = bwo.get_action()
        if action_name is not None:
            found_actions.append(action_name)

    # Get "real" action name only once per action
    for action_name in set(found_actions):
        if action_name not in current_workflows_ui.actions:
            # Perhaps some old action? Use stored name.
            action_nicename = action_name
        else:
            action = current_workflows_ui.actions[action_name]
            action_nicename = getattr(action, "name", action_name)
        action_dict[action_nicename] = found_actions.count(action_name)
    return action_dict


def get_rendered_row(obj_id):
    """Return a single formatted row."""
    bwo = WorkflowObject.query.get(obj_id)  # noqa
    if not bwo:
        current_app.logger.error("workflow object not found for {0}".format(obj_id))
        return ""
    preformatted = get_formatted_holdingpen_object(bwo)
    return render_template(
        'invenio_workflows_ui/list_row.html',
        title=preformatted.get("title", ""),
        object=bwo,
        action=preformatted.get("action", ""),
        description=preformatted.get("description", ""),
        additional=preformatted.get("additional", "")
    )


def get_rows(id_list):
    """Return all rows formatted."""
    return [get_rendered_row(bid)
            for bid in id_list]


def get_previous_next_objects(object_list, current_object_id):
    """Return tuple of (previous, next) object for given Holding Pen object."""
    if not object_list:
        return None, None
    try:
        current_index = object_list.index(current_object_id)
    except ValueError:
        # current_object_id not in object_list:
        return None, None
    try:
        next_object_id = object_list[current_index + 1]
    except IndexError:
        next_object_id = None
    try:
        if current_index == 0:
            previous_object_id = None
        else:
            previous_object_id = object_list[current_index - 1]
    except IndexError:
        previous_object_id = None
    return previous_object_id, next_object_id


def get_task_history(last_task):
    """Append last task to task history."""
    if hasattr(last_task, 'branch') and last_task.branch:
        return
    elif hasattr(last_task, 'hide') and last_task.hide:
        return
    else:
        return get_func_info(last_task)


def get_func_info(func):
    """Retrieve a function's information."""
    name = func.func_name
    doc = func.func_doc or ""
    try:
        nicename = func.description
    except AttributeError:
        if doc:
            nicename = doc.split('\n')[0]
            if len(nicename) > 80:
                nicename = name
        else:
            nicename = name
    parameters = []
    closure = func.func_closure
    varnames = func.func_code.co_freevars
    if closure:
        for index, arg in enumerate(closure):
            if not callable(arg.cell_contents):
                parameters.append((varnames[index],
                                   text_type(arg.cell_contents)))
    return ({
        "nicename": nicename,
        "doc": doc,
        "parameters": parameters,
        "name": name
    })


def get_workflow_info(func_list):
    """Return function info, go through lists recursively."""
    funcs = []
    for item in func_list:
        if item is None:
            continue
        if isinstance(item, list):
            funcs.append(get_workflow_info(item))
        else:
            funcs.append(get_func_info(item))
    return funcs
