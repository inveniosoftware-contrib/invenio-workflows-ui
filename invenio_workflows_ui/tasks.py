# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Celery Tasks proxy to the state object."""

from __future__ import absolute_import, print_function

from celery import shared_task


@shared_task(ignore_result=True)
def resolve_actions(object_ids, action, *args, **kwargs):
    """Resolve a set of actions."""
    from invenio_workflows import WorkflowObject
    from invenio_workflows_ui import workflow_api_class, actions

    for id_object in object_ids:
        workflow_object = WorkflowObject.query.get(id_object)
        if workflow_object:
            workflow_ui_object = workflow_api_class.create(workflow_object)
            getattr(workflow_ui_object, action)(*args, **kwargs)
