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

"""UI layer for invenio-workflows."""

from __future__ import absolute_import, print_function

import pkg_resources

from . import config
from .views import rest, ui
from .search import WorkflowUISearch


class _WorkflowsUIState(object):
    """WorkflowsUI state storing registered actions."""

    def __init__(self, app, entry_point_group=None, cache=None):
        """Initialize state."""
        self.app = app
        self.actions = {}
        self.cache = cache
        self.searcher = WorkflowUISearch.create(app)
        if entry_point_group:
            self.load_entry_point_group(entry_point_group)

    def set(self, key, value):
        """Store value in cache by key."""
        if self.cache:
            self.cache.set(
                self.app.config['WORKFLOWS_UI_CACHE_PREFIX'] +
                str(key), value
            )

    def get(self, key):
        """Get value in cache by key."""
        data = None
        if self.cache:
            data = self.cache.get(
                self.app.config['WORKFLOWS_UI_CACHE_PREFIX'] +
                str(key)
            )
        return data

    def delete(self, key):
        """Delete key from cache."""
        if self.cache:
            self.cache.delete(
                self.app.config['WORKFLOWS_UI_CACHE_PREFIX'] +
                str(key)
            )

    def register_action(self, name, action):
        """Register an action to be showed in the actions list."""
        assert name not in self.actions
        self.actions[name] = action

    def load_entry_point_group(self, entry_point_group):
        """Load actions from an entry point group."""
        for ep in pkg_resources.iter_entry_points(group=entry_point_group):
            self.register_action(ep.name, ep.load())


class InvenioWorkflowsUIREST(object):
    """invenio-workflows-ui extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        if app:
            self._state = self.init_app(app, **kwargs)

    def init_app(self, app,
                 entry_point_group='invenio_workflows_ui.actions',
                 **kwargs):
        """Flask application initialization."""
        from invenio_records_rest.views import create_blueprint

        self.init_config(app)
        # app.register_blueprint(blueprint)
        app.register_blueprint(rest.create_blueprint(
            app.config['WORKFLOWS_UI_REST_ENDPOINTS']
        ))
        state = _WorkflowsUIState(app, entry_point_group=entry_point_group,
                                  cache=kwargs.get('cache'))
        app.extensions['invenio-workflows-ui-rest'] = state
        return state

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            "WORKFLOWS_UI_BASE_TEMPLATE",
            app.config.get("BASE_TEMPLATE",
                           "invenio_workflows_ui/base.html"))
        app.config.setdefault("WORKFLOWS_UI_CACHE_PREFIX",
                              "WorkflowsUI::")
        app.config.setdefault("WORKFLOWS_UI_LIST_TEMPLATE",
                              "invenio_workflows_ui/list.html")
        app.config.setdefault("WORKFLOWS_UI_DETAILS_TEMPLATE",
                              "invenio_workflows_ui/details.html")
        app.config.setdefault("WORKFLOWS_UI_LIST_ROW_TEMPLATE",
                              "invenio_workflows_ui/list_row.html")
        app.config.setdefault("WORKFLOWS_UI_INDEX_TEMPLATE",
                              "invenio_workflows_ui/index.html")
        for k in dir(config):
            if k.startswith('WORKFLOWS_UI_'):
                app.config.setdefault(k, getattr(config, k))

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(self._state, name, None)


class InvenioWorkflowsUI(object):
    """invenio-workflows-ui extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        if app:
            self._state = self.init_app(app, **kwargs)

    def init_app(self, app,
                 entry_point_group='invenio_workflows_ui.actions',
                 **kwargs):
        """Flask application initialization."""
        self.init_config(app)
        app.register_blueprint(ui.blueprint)
        state = _WorkflowsUIState(app, entry_point_group=entry_point_group,
                                  cache=kwargs.get('cache'))
        app.extensions['invenio-workflows-ui'] = state
        return state

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            "WORKFLOWS_UI_BASE_TEMPLATE",
            app.config.get("BASE_TEMPLATE",
                           "invenio_workflows_ui/base.html"))
        app.config.setdefault("WORKFLOWS_UI_CACHE_PREFIX",
                              "WorkflowsUI::")
        app.config.setdefault("WORKFLOWS_UI_LIST_TEMPLATE",
                              "invenio_workflows_ui/list.html")
        app.config.setdefault("WORKFLOWS_UI_DETAILS_TEMPLATE",
                              "invenio_workflows_ui/details.html")
        app.config.setdefault("WORKFLOWS_UI_LIST_ROW_TEMPLATE",
                              "invenio_workflows_ui/list_row.html")
        app.config.setdefault("WORKFLOWS_UI_INDEX_TEMPLATE",
                              "invenio_workflows_ui/index.html")
        for k in dir(config):
            if k.startswith('WORKFLOWS_UI_'):
                app.config.setdefault(k, getattr(config, k))

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(self._state, name, None)
