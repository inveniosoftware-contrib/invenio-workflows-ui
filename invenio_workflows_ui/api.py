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
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API."""

from __future__ import absolute_import, print_function

import six

from flask import current_app

from elasticsearch import TransportError

from invenio_db import db
from invenio_records import Record
from invenio_workflows import ObjectStatus, WorkflowObject, resume
from invenio_workflows.proxies import workflows

from invenio_search import current_search_client

from .proxies import actions


class WorkflowUIRecord(Record):
    """Represents a workflow object record for indexing."""

    @classmethod
    def create(cls, workflow_object, **kwargs):
        """Create a indexable workflow JSON."""
        record = cls.record_from_model(workflow_object)
        return cls(record, model=workflow_object, **kwargs)

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Get record instance.
        Raises database exception if record does not exists.
        """
        with db.session.no_autoflush:
            query = WorkflowObject.query.filter_by(id=id_)
            obj = query.one()
            return cls(cls.record_from_model(obj), model=obj)

    @staticmethod
    def record_from_model(workflow_object):
        """Build data from workflow object.

        NOTE: This entire function may in principle be in invenio_workflows
        WorkflowObject model as a to_dict() kind of function of the model.
        """
        record = {}
        record["id"] = workflow_object.id
        record["_workflow"] = {}
        record["_workflow"]["data_type"] = workflow_object.data_type
        record["_workflow"]["status"] = ObjectStatus.labels[workflow_object.status.value]
        record["_workflow"]["created"] = workflow_object.created.isoformat()
        record["_workflow"]["modified"] = workflow_object.modified.isoformat()
        record["_workflow"]["id_user"] = workflow_object.id_user
        record["_workflow"]["id_parent"] = workflow_object.id_parent
        record["_workflow"]["id_workflow"] = None
        record["_workflow"]["workflow_class"] = None
        record["_workflow"]["workflow_position"] = None
        record["_workflow"]["workflow_name"] = None

        if workflow_object.workflow and workflow_object.workflow.name in workflows:
            workflow_definition = workflows.get(workflow_object.workflow.name)

            if not record["_workflow"]["data_type"] and workflow_definition and hasattr(
                    workflow_definition, 'data_type'):
                record["_workflow"]["data_type"] = workflow_definition.data_type

            if workflow_definition and hasattr(workflow_definition, 'name'):
                record["_workflow"]["workflow_name"] = workflow_definition.name

            if workflow_object.id_workflow:
                record["_workflow"]["id_workflow"] = six.text_type(workflow_object.id_workflow)

            record["_workflow"]["workflow_class"] = workflow_object.workflow.name
            record["_workflow"]["workflow_position"] = six.text_type(workflow_object.callback_pos)

        if isinstance(workflow_object.data, dict):
            record.update(workflow_object.data)
        return record

    def resolve(self, *args, **kwargs):
        """Resolve an action if applicable."""
        action_name = self.model.get_action()
        if action_name:
            action_form = actions[action_name]
            return action_form.resolve(self.model, *args, **kwargs)

    def restart(self, *args, **kwargs):
        """Resume execution from current task/callback in workflow."""
        return resume.delay(
            oid=self.model.id,
            restart_point="restart_task"
        ).id

    def resume(self, *args, **kwargs):
        """Resume execution from next task/callback in workflow."""
        return resume.delay(
            oid=self.model.id,
            restart_point="continue_task"
        ).id

    def index(self, index_name=None, doc_type=None):
        """Index the workflow record into desired index/doc_type."""
        config = current_app.config['WORKFLOWS_UI_DATA_TYPES'].get(
            self["_workflow"]["data_type"]
        )
        if config or (index_name and doc_type):
            try:
                current_search_client.index(
                    id=str(self['id']),
                    index=index_name or config.get('search_index'),
                    doc_type=doc_type or config.get('search_type'),
                    body=self.dumps(),
                )
            except TransportError:
                current_app.logger.exception()
                current_app.logger.error(
                    "Problem while indexing workflow object {0}".format(
                        self.model.id
                    )
                )

    def delete_from_index(self, index=None, doc_type=None):
        """Delete given record from index."""
        config = current_app.config['WORKFLOWS_UI_DATA_TYPES'].get(
            self["_workflow"]["data_type"]
        )
        if config or (index and doc_type):
            try:
                current_search_client.delete(
                    index=index or config.get('search_index'),
                    doc_type=doc_type or config.get('search_type'),
                    id=str(self['id']),
                    ignore=404
                )
            except TransportError:
                current_app.logger.exception()
                current_app.logger.error(
                    "Problem while indexing workflow object {0}".format(
                        self.model.id
                    )
                )
