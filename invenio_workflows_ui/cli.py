# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

"""CLI for invenio-workflows-ui."""

from __future__ import absolute_import, print_function

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_workflows.models import WorkflowObjectModel
from time import sleep

from .tasks import batch_reindex


@click.group()
def holdingpen():
    """Manage holdingpen."""


def next_batch(iterator, batch_size):
    """Get first batch_size elements from the iterable, or remaining if less.

    :param iterator: the iterator for the iterable
    :param batch_size: size of the requested batch
    :return: batch (list)
    """
    batch = []

    try:
        for idx in range(batch_size):
            batch.append(next(iterator))
    except StopIteration:
        pass

    return batch


@holdingpen.command()
@click.option('--yes-i-know', is_flag=True)
@click.option('-t', '--data-type', multiple=True, required=True)
@click.option('-s', '--batch-size', default=200)
@click.option('-q', '--queue-name', default='indexer_task')
@with_appcontext
def reindex(yes_i_know, data_type, batch_size, queue_name):
    """Reindex all records in a parallel manner.

    :param yes_i_know: if True, skip confirmation screen
    :param data_type: workflow data type.
    :param batch_size: number of documents per batch sent to workers.
    :param queue_name: name of the celery queue
    """
    if not yes_i_know:
        click.confirm(
            'Do you really want to reindex the workflows?',
            abort=True,
        )

    click.secho('Sending workflows to the indexing queue...', fg='green')

    query = (
        db.session.query(WorkflowObjectModel.id)
        .filter(WorkflowObjectModel.data_type.in_(data_type))
    )
    request_timeout = current_app.config.get('INDEXER_BULK_REQUEST_TIMEOUT')
    all_tasks = []

    with click.progressbar(
        query.yield_per(2000),
        length=query.count(),
        label='Scheduling indexing tasks'
    ) as items:
        batch = next_batch(items, batch_size)

        while batch:
            task = batch_reindex.apply_async(
                kwargs={
                    'workflow_ids': [item[0] for item in batch],
                    'request_timeout': request_timeout,
                },
                queue=queue_name,
            )

            all_tasks.append(task)
            batch = next_batch(items, batch_size)

    click.secho('Created {} tasks.'.format(len(all_tasks)), fg='green')

    with click.progressbar(
        length=len(all_tasks),
        label='Indexing workflows'
    ) as progressbar:
        def _finished_tasks_count():
            return len(filter(lambda task: task.ready(), all_tasks))

        while len(all_tasks) != _finished_tasks_count():
            sleep(0.5)
            # this is so click doesn't divide by 0:
            progressbar.pos = _finished_tasks_count() or 1
            progressbar.update(0)

    successes = sum([task.result.get('success', 0) for task in all_tasks])
    failures = sum([task.result.get('failures', []) for task in all_tasks], [])

    color = 'red' if failures else 'green'
    click.secho(
        'Reindexing failed for {} records, succeeded for {}.'.format(
            len(failures),
            successes
        ),
        fg=color,
    )

    log_path = '/tmp/holdingpen_index.err'
    with open(log_path, 'w') as log:
        for failure in failures:
            log.write('%s\n' % repr(failure))

    if failures:
        click.secho('You can see the errors in %s' % log_path)
