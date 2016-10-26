# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""UI layer for invenio-workflows.

workflows UI is a web interface overlay for all WorkflowObject's.

This area is targeted to catalogers and administrators for inspecting
and reacting to workflows executions. More importantly, allowing users to deal
with halted workflows.

For example, accepting submissions or other tasks.
"""

from __future__ import absolute_import, print_function

from flask import (
    Blueprint,
    abort,
    render_template,
    current_app
)

from flask_login import login_required

from invenio_workflows.errors import WorkflowsMissingObject

from invenio_workflows.proxies import workflow_object_class

from ..utils import (
    obj_or_import_string
)
from ..permissions import admin_permission_factory


def create_blueprint(config, url_endpoint, context_processors):
    """Create UI blueprint for invenio-workflows-ui."""
    blueprint = Blueprint(
        'invenio_workflows_ui',
        __name__,
        url_prefix=url_endpoint,
        template_folder='../templates',
        static_folder='../static',
    )

    @blueprint.route('/', methods=['GET', 'POST'])
    @blueprint.route('/index', methods=['GET', 'POST'])
    @login_required
    def index():
        """Display basic dashboard interface of Workflows UI."""
        if not admin_permission_factory().can():
            abort(403)
        return render_template(
            current_app.config['WORKFLOWS_UI_INDEX_TEMPLATE']
        )

    @blueprint.route('/list', methods=['GET', ])
    @blueprint.route('/list/', methods=['GET', ])
    @blueprint.route('/list/<search_value>', methods=['GET', ])
    @login_required
    def list_objects(search_value=None):
        """Display main table interface of workflows UI."""
        if not admin_permission_factory().can():
            abort(403)
        return render_template(
            current_app.config['WORKFLOWS_UI_LIST_TEMPLATE'],
            search=search_value
        )

    @blueprint.route('/<int:objectid>', methods=['GET', 'POST'])
    @blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
    @login_required
    def details(objectid):
        """Display info about the object."""
        if not admin_permission_factory().can():
            abort(403)
        try:
            workflow_object = workflow_object_class.get(objectid)
        except WorkflowsMissingObject:
            abort(404)

        return render_template(
            current_app.config['WORKFLOWS_UI_DETAILS_TEMPLATE'],
            workflow_object=workflow_object,
        )

    for proc in context_processors:
        blueprint.context_processor(obj_or_import_string(proc))

    return blueprint
