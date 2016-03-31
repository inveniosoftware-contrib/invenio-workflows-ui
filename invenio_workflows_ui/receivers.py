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

from flask import current_app
from sqlalchemy.event import listen

from invenio_workflows.models import DbWorkflowObject, ObjectStatus
from invenio_workflows.signals import workflow_object_saved


def delete_from_index(mapper, connection, target):
    """Delete record from index."""
    from invenio_search import current_search_client as es

    indices = set(current_app.config.get(
        'SEARCH_ELASTIC_COLLECTION_INDEX_MAPPING').values())
    indices.add(current_app.config.get('SEARCH_ELASTIC_DEFAULT_INDEX'))

    doc_type = current_app.config.get(
        "WORKFLOWS_HOLDING_PEN_DOC_TYPE"
    )
    for index in indices:
        index = current_app.config.get(
            'WORKFLOWS_HOLDING_PEN_ES_PREFIX') + index
        es.delete(
            index=index,
            doc_type=doc_type,
            id=target.id,
            ignore=404
        )


@workflow_object_saved.connect
def index_holdingpen_record(sender, **kwargs):
    """Index a Holding Pen record."""
    from invenio_search import current_search_client as es
    from invenio_records.api import Record

    from invenio_workflows.proxies import workflows

    if not sender.workflow:
        # No workflow registered to object yet. Skip indexing
        return

    if sender.status == DbWorkflowObject.known_statuses.INITIAL:
        # Ignore initial status
        return

    workflow = workflows.get(sender.workflow.name)
    if not workflow:
        current_app.logger.error(
            "No workflow found for sender: {0}".format(sender.id)
        )
        return

    if not hasattr(sender, 'data'):
        sender.data = sender.get_data()
    if not hasattr(sender, 'extra_data'):
        sender.extra_data = sender.get_extra_data()

    record = Record({})
    record["type"] = sender.data_type
    record["status"] = ObjectStatus.labels[sender.status.value]
    record["created"] = sender.created.isoformat()
    record["modified"] = sender.modified.isoformat()
    record["uri"] = sender.uri
    record["id_workflow"] = sender.id_workflow
    record["id_user"] = sender.id_user
    record["id_parent"] = sender.id_parent
    record["workflow"] = sender.workflow.name
    try:
        record.update(workflow.get_record(sender))
    except Exception as err:
        current_app.logger.exception(err)

    try:
        record.update(workflow.get_sort_data(sender))
    except Exception as err:
        current_app.logger.exception(err)



    # Trigger any before_record_index receivers
    # before_record_update.send(sender.id, json=record, index=workflow)

    index = current_app.config.get(
        'WORKFLOWS_HOLDING_PEN_ES_PREFIX',
        "holdingpen_") + workflow.object_type.replace(" ", "_").lower()
    es.index(
        index=index,
        doc_type=current_app.config.get("WORKFLOWS_HOLDING_PEN_DOC_TYPE",
                                        "WORKFLOWS_HOLDING_PEN_DOC_TYPE"),
        body=dict(record),
        id=sender.id
    )


listen(DbWorkflowObject, "after_delete", delete_from_index)
