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

"""Celery Tasks."""

from __future__ import absolute_import, print_function

import elasticsearch
from celery import shared_task
from celery.utils.log import get_task_logger
from invenio_search import current_search_client
from invenio_workflows.api import WorkflowObject
from invenio_workflows.errors import WorkflowsError

from .proxies import workflow_api_class


LOGGER = get_task_logger(__name__)


@shared_task(ignore_result=True)
def resolve_actions(object_ids, action, *args, **kwargs):
    """Resolve a set of actions."""
    from invenio_workflows_ui import workflow_api_class

    for id_object in object_ids:
        workflow_ui_object = workflow_api_class.get_record(id_object)
        if workflow_ui_object:
            getattr(workflow_ui_object, action)(*args, **kwargs)


@shared_task(ignore_result=False)
def batch_reindex(workflow_ids, request_timeout):
    """Task for bulk reindexing workflow records."""
    indexer = workflow_api_class.indexer

    def actions():
        for workflow_id in workflow_ids:
            try:
                workflow_object = WorkflowObject.get(workflow_id)
                record = workflow_api_class.record_from_object(workflow_object)
                workflow_api_object = workflow_api_class(
                    record,
                    workflow=workflow_object,
                )
                index, doc_type = indexer.record_to_index(workflow_api_object)
                body = indexer._prepare_record(
                    workflow_api_object,
                    index,
                    doc_type,
                )
                yield {
                    '_id': workflow_api_object.id,
                    '_index': index,
                    '_type': doc_type,
                    '_op_type': 'index',
                    '_source': body,
                }
            except WorkflowsError as e:
                LOGGER.warn('Workflow %s failed to load: %s', workflow_id, e)

    success, failures = elasticsearch.helpers.bulk(
        current_search_client,
        actions(),
        request_timeout=request_timeout,
        raise_on_error=False,
        raise_on_exception=False,
        max_retries=5,
        initial_backoff=10,
    )

    return {
        'success': success,
        'failures': [repr(failure) for failure in failures or []]
    }
