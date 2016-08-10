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

from functools import partial, wraps

from flask import current_app, request

from elasticsearch import TransportError

from invenio_db import db

from invenio_records import Record
from invenio_records.errors import MissingModelError

from invenio_workflows import ObjectStatus, resume
from invenio_workflows.proxies import workflows, workflow_object_class

from .proxies import actions
from .indexer import WorkflowIndexer


def record_to_index(record):
    """Index the workflow record into desired index/doc_type."""
    config = current_app.config['WORKFLOWS_UI_DATA_TYPES'].get(
        record["_workflow"]["data_type"]
    )
    if not config:
        return None, None
    return config.get('search_index'), config.get('search_type')


def index(method=None, delete=False):
    """Apply to API methods that need to change the index for the object."""
    # Check if we shall save arguments and recreate decorator
    if method is None:
        return partial(index, delete=delete)

    @wraps(method)
    def wrapper(self_or_cls, *args, **kwargs):
        """Send record for indexing."""
        result = method(self_or_cls, *args, **kwargs)
        try:
            if delete:
                self_or_cls.indexer.delete(result)
            else:
                self_or_cls.indexer.index(result)
        except TransportError as err:
            current_app.logger.exception(err)
            current_app.logger.error(
                "Problem while indexing workflow object {0}".format(
                    self_or_cls.id
                )
            )
        return result
    return wrapper


class WorkflowUIRecord(Record):
    """Represents a workflow object record for indexing."""

    indexer = WorkflowIndexer(
        record_to_index=record_to_index,
    )

    @classmethod
    @index
    def create(cls, workfow_model, **kwargs):
        """Create a indexable workflow JSON."""
        record = cls.record_from_model(workfow_model)
        return cls(record, model=workfow_model, **kwargs)

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Get record instance.
        Raises database exception if record does not exists.
        """
        with db.session.no_autoflush:
            obj = workflow_object_class.get(id_).model
            return cls(cls.record_from_model(obj), model=obj)

    def commit(self):
        """Commit a change to the record state."""
        with db.session.begin_nested():
            self.update_model()

    def delete(self, force=False):
        """Delete model from DB and search index (the index is deleted using
        a signal, see the `receivers` module)."""
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            db.session.delete(self.model)
        return self

    @staticmethod
    def record_from_model(workfow_model):
        """Build data from workflow object.

        NOTE: This entire function may in principle be in
        workflow_object_class model as a to_dict() kind of function of
        the model.
        """
        record = {}
        record["id"] = workfow_model.id
        record["_workflow"] = {}
        record["_workflow"]["data_type"] = workfow_model.data_type
        record["_workflow"]["status"] = workfow_model.status.name
        record["_workflow"]["id_user"] = workfow_model.id_user
        record["_workflow"]["id_parent"] = workfow_model.id_parent
        record["_workflow"]["id_workflow"] = None
        record["_workflow"]["workflow_class"] = None
        record["_workflow"]["workflow_position"] = workfow_model.callback_pos
        record["_workflow"]["workflow_name"] = None

        if workfow_model.workflow and workfow_model.workflow.name in workflows:
            workflow_definition = workflows.get(workfow_model.workflow.name)

            if not record["_workflow"]["data_type"] and workflow_definition and hasattr(
                    workflow_definition, 'data_type'):
                record["_workflow"]["data_type"] = workflow_definition.data_type

            if workflow_definition and hasattr(workflow_definition, 'name'):
                record["_workflow"]["workflow_name"] = workflow_definition.name

            if workfow_model.id_workflow:
                record["_workflow"]["id_workflow"] = six.text_type(workfow_model.id_workflow)

            record["_workflow"]["workflow_class"] = workfow_model.workflow.name

        if isinstance(workfow_model.data, dict):
            record.update({"metadata": workfow_model.data})
        if isinstance(workfow_model.extra_data, dict):
            record.update({"_extra_data": workfow_model.extra_data})
        return record

    def update_model(self):
        """Update model from current record."""
        if self.model is None:
            raise MissingModelError()

        self.model.data_type = self["_workflow"]["data_type"]
        self.model.status = ObjectStatus[self["_workflow"]["status"]]
        self.model.id_user = self["_workflow"]["id_user"]
        self.model.id_parent = self["_workflow"]["id_parent"]
        self.model.id_workflow = self["_workflow"]["id_workflow"]
        self.model.callback_pos = self["_workflow"]["workflow_position"]
        self.model.data = self['metadata']
        self.model.extra_data = self['_extra_data']
        self.model.save()

    def edit(self, *args, **kwargs):
        """Edit and save record (automatically indexed)."""
        record = request.json
        if record:
            self.update(record)
            self.commit()
        return self

    def restart(self, *args, **kwargs):
        """Resume execution from current task/callback in workflow."""
        if self.model is None:
            raise MissingModelError()

        if 'callback_pos' in kwargs:
            self.model.callback_pos = kwargs['callback_pos']
            self.model.save()
            db.session.commit()
        return resume.delay(
            oid=self.model.id,
            restart_point="restart_task"
        ).id

    def resume(self, *args, **kwargs):
        """Resume execution from next task/callback in workflow."""
        if self.model is None:
            raise MissingModelError()

        if 'callback_pos' in kwargs:
            self.model.callback_pos = kwargs['callback_pos']
            self.model.save()
            db.session.commit()
        return resume.delay(
            oid=self.model.id,
            restart_point="continue_next"
        ).id

    def resolve(self, *args, **kwargs):
        """Resolve an action if applicable."""
        if self.model is None:
            raise MissingModelError()

        action_name = self.model.get_action()
        if action_name:
            action_form = actions[action_name]
            return action_form.resolve(self.model, *args, **kwargs)

    @property
    def revision_id(self):
        """Special override as workflow object does not have revision."""
        return None

    @property
    def files(self):
        """Adapter for self.model files object."""
        return self.model.files
