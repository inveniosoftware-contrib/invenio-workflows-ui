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
from flask.cli import with_appcontext

from invenio_workflows.api import WorkflowObject
from invenio_workflows.models import WorkflowObjectModel

from .proxies import workflow_api_class


@click.group()
def holdingpen():
    """Manage holdingpen."""


@holdingpen.command()
@click.option('--yes-i-know', is_flag=True)
@click.option('-t', '--data-type', multiple=True, required=True)
@with_appcontext
def reindex(yes_i_know, data_type):
    """Reindex all records.

    :param data_type: workflow data type.
    """
    if not yes_i_know:
        click.confirm('Do you really want to reindex all records?', abort=True)

    click.secho('Sending records to indexing queue ...', fg='green')

    query = WorkflowObjectModel.query.filter(
        WorkflowObjectModel.data_type.in_(data_type)
    )

    with click.progressbar(query) as q:
        for result in q:
            workflow_object = WorkflowObject.get(result.id)
            workflow_api_class.create(workflow_object)
