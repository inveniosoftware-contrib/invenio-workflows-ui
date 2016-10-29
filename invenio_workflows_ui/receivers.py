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

from elasticsearch.exceptions import NotFoundError
from invenio_workflows.models import WorkflowObjectModel
from invenio_workflows.signals import workflow_object_after_save
from sqlalchemy.event import listen

from .proxies import workflow_api_class


def delete_from_index(mapper, connection, target):
    """Delete workflow object from index."""
    obj = workflow_api_class.get_record(target.id)
    try:
        workflow_api_class.indexer.delete(obj)
    except NotFoundError:
        return


@workflow_object_after_save.connect
def index_workflow_object(sender, **kwargs):
    """Index a workflow object for workflows UI."""
    workflow_api_class.create(sender)

listen(WorkflowObjectModel, "before_delete", delete_from_index)
