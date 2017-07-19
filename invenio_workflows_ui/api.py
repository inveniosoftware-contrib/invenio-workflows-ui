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

from functools import partial, wraps

import six
from elasticsearch import TransportError
from flask import current_app, request
from invenio_db import db
from invenio_records import Record
from invenio_records.errors import MissingModelError
from invenio_workflows import ObjectStatus, resume
from invenio_workflows.proxies import workflow_object_class, workflows
from workflow.engine_db import WorkflowStatus

from .indexer import WorkflowIndexer
from .proxies import actions


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

    def __init__(self, *args, **kwargs):
        """Represent a workflow object record for indexing."""
        try:
            self.workflow = kwargs.pop('workflow')
        except KeyError:
            raise TypeError(
                'WorkflowUIRecord.__init__ missing workflow argument'
            )

        kwargs['model'] = self.workflow.model
        super(WorkflowUIRecord, self).__init__(*args, **kwargs)

    @classmethod
    @index
    def create(cls, workflow_object, **kwargs):
        """Create a indexable workflow JSON."""
        record = cls.record_from_object(workflow_object)
        return cls(record, workflow=workflow_object, **kwargs)

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Get record instance.

        Raises database exception if record does not exists.
        """
        with db.session.no_autoflush:
            obj = workflow_object_class.get(id_)
            return cls(cls.record_from_object(obj), workflow=obj)

    def commit(self):
        """Commit a change to the record state."""
        with db.session.begin_nested():
            self.update_model()

    def delete(self, force=False):
        """Delete model from DB and search index.

        The index is deleted using a signal, see the `receivers` module).
        """
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            db.session.delete(self.model)
        return self

    @staticmethod
    def record_from_object(workflow_object):
        """Build data from workflow object.

        NOTE: This entire function may in principle be in
        workflow_object_class model as a to_dict() kind of function of
        the model.
        """
        record = {}
        record["id"] = workflow_object.id
        _workflow = {}
        _workflow["data_type"] = workflow_object.data_type
        _workflow["status"] = workflow_object.status.name
        _workflow["id_user"] = workflow_object.id_user
        _workflow["id_parent"] = workflow_object.id_parent
        _workflow["id_workflow"] = None
        _workflow["workflow_class"] = None
        _workflow["workflow_position"] = workflow_object.callback_pos
        _workflow["workflow_name"] = None

        if (
                workflow_object.workflow and
                workflow_object.workflow.name in workflows
        ):
            workflow_definition = workflows.get(workflow_object.workflow.name)

            if (
                    not _workflow["data_type"] and
                    workflow_definition and
                    hasattr(workflow_definition, 'data_type')
            ):
                _workflow["data_type"] = workflow_definition.data_type

            if workflow_definition and hasattr(workflow_definition, 'name'):
                _workflow["workflow_name"] = workflow_definition.name

            if workflow_object.id_workflow:
                _workflow["id_workflow"] = six.text_type(
                    workflow_object.id_workflow
                )

            _workflow["workflow_class"] = workflow_object.workflow.name

        if isinstance(workflow_object.data, dict):
            record.update({"metadata": workflow_object.data})
        if isinstance(workflow_object.extra_data, dict):
            record.update({"_extra_data": workflow_object.extra_data})

        record["_workflow"] = _workflow
        return record

    def update_model(self):
        """Update model from current record."""
        if self.model is None:
            raise MissingModelError()

        self.workflow.data_type = self["_workflow"]["data_type"]
        self.workflow.status = ObjectStatus[self["_workflow"]["status"]]
        self.workflow.id_user = self["_workflow"]["id_user"]
        self.workflow.id_parent = self["_workflow"]["id_parent"]
        self.workflow.id_workflow = self["_workflow"]["id_workflow"]
        self.workflow.callback_pos = self["_workflow"]["workflow_position"]
        self.workflow.data = self['metadata']
        self.workflow.extra_data = self['_extra_data']
        self.workflow.save()

    def edit(self, *args, **kwargs):
        """Edit and save record (automatically indexed)."""
        record = request.json
        if record:
            self.update(record)
            self.commit()
        return self

    def restart(self, *args, **kwargs):
        """Restart the whole workflow.

        Params:
            callback_pos(list(int)): if passed will restart the workflow from
                the given callback_pos instead of restarting from scratch.

        """
        if self.model is None:
            raise MissingModelError()

        if 'callback_pos' in kwargs:
            self.workflow.callback_pos = kwargs['callback_pos']
        else:
            self.workflow.callback_pos = [0]

        self.workflow.status = ObjectStatus[WorkflowStatus.RUNNING.name]
        self.workflow.save()
        db.session.commit()
        return resume.delay(
            oid=self.workflow.id,
            restart_point="restart_task"
        ).id

    def resume(self, *args, **kwargs):
        """Resume execution from next task/callback in workflow."""
        if self.model is None:
            raise MissingModelError()

        if 'callback_pos' in kwargs:
            self.workflow.callback_pos = kwargs['callback_pos']

        self.workflow.status = ObjectStatus[WorkflowStatus.RUNNING.name]
        self.workflow.save()
        db.session.commit()
        return resume.delay(
            oid=self.id,
            restart_point="continue_next"
        ).id

    def resolve(self, *args, **kwargs):
        """Resolve an action if applicable."""
        if self.model is None:
            raise MissingModelError()

        action_name = self.workflow.get_action()
        if action_name:
            action_form = actions[action_name]
            return action_form.resolve(self.workflow, *args, **kwargs)

    @property
    def revision_id(self):
        """Override as workflow object does not have revision."""
        return None

    @property
    def files(self):
        """Adapter for self.workflow files object."""
        return self.workflow.files
