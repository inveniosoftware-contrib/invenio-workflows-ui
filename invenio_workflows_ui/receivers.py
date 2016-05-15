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

"""Signal receivers for workflows."""

from __future__ import absolute_import, print_function

from sqlalchemy.event import listen

from invenio_workflows import WorkflowObject
from invenio_workflows.signals import workflow_object_saved

from .api import WorkflowUIRecord


def delete_from_index(mapper, connection, target):
    """Delete workflow object from index."""
    obj = WorkflowUIRecord.create(target)
    obj.delete_from_index()


@workflow_object_saved.connect
def index_workflow_object(sender, **kwargs):
    """Index a workflow object for workflows UI."""
    obj = WorkflowUIRecord.create(sender)
    obj.index()


listen(WorkflowObject, "before_delete", delete_from_index)
