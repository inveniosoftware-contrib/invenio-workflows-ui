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

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_workflows import ObjectStatus, WorkflowObject
from invenio_workflows.proxies import workflows

from invenio_search import current_search_client

from .errors import WorkflowUISkipIndexing
from .minters import workflow_minter


class WorkflowUIRecord(Record):
    """Represents a workflow object record for indexing."""

    @classmethod
    def create(cls, workflow_object, **kwargs):
        """Create a indexable workflow JSON."""
        if not workflow_object.workflow:
            # No workflow registered to object yet. Skip indexing
            raise WorkflowUISkipIndexing("Workflow does not exist")

        if workflow_object.status == WorkflowObject.known_statuses.INITIAL:
            # Ignore initial status
            raise WorkflowUISkipIndexing("Status is INITIAL")

        if workflow_object.workflow.name not in workflows:
            raise WorkflowUISkipIndexing(
                "No workflow {0} found for {1}".format(
                    workflow_object.name, workflow_object.id
                )
            )
        record = cls.build_from_workflow_object(workflow_object)
        return cls(record, **kwargs)

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Get record instance.
        Raises database exception if record does not exists.
        """
        with db.session.no_autoflush:
            query = WorkflowObject.query.filter_by(id=id_)
            obj = query.one()
            return cls(cls.build_from_workflow_object(obj))

    @staticmethod
    def build_from_workflow_object(workflow_object):
        """Build data from workflow object."""
        workflow_definition = workflows.get(workflow_object.workflow.name)
        record = {}
        record["id"] = workflow_object.id
        if not workflow_object.data_type:
            if hasattr(workflow_definition, 'data_type'):
                data_type = workflow_definition.data_type
            else:
                data_type = "workflow"
        else:
            data_type = workflow_object.data_type
        record["_workflow"] = {}
        record["_workflow"]["data_type"] = data_type
        record["_workflow"]["status"] = ObjectStatus.labels[workflow_object.status.value]
        record["_workflow"]["created"] = workflow_object.created.isoformat()
        record["_workflow"]["modified"] = workflow_object.modified.isoformat()
        record["_workflow"]["id_workflow"] = six.text_type(workflow_object.id_workflow)
        record["_workflow"]["id_user"] = workflow_object.id_user
        record["_workflow"]["id_parent"] = workflow_object.id_parent
        record["_workflow"]["workflow"] = workflow_object.workflow.name

        if isinstance(workflow_object.data, dict):
            record.update(workflow_object.data)
        return record

    def index(self, index_name=None, doc_type=None):
        """Index the workflow record into desired index/doc_type."""
        config = current_app.config['WORKFLOWS_UI_DATA_TYPES'].get(
            self["_workflow"]["data_type"]
        )
        if config or (index_name and doc_type):
            current_search_client.index(
                id=str(self['id']),
                index=index_name or config.get('search_index'),
                doc_type=doc_type or config.get('search_type'),
                body=self.dumps(),
            )

    @staticmethod
    def delete_from_index(workflow_object, index=None, doc_type=None):
        """Delete given record from index."""
        config = current_app.config['WORKFLOWS_UI_DATA_TYPES'].get(
            self["_workflow"]["data_type"]
        )
        if config or (index_name and doc_type):
            current_search_client.delete(
                index=index or config.get('search_index'),
                doc_type=doc_type or config.get('search_type'),
                id=workflow_object.id,
                ignore=404
            )
