# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Workflows bundles."""

from __future__ import absolute_import, print_function

from flask_assets import Bundle

from invenio_assets import NpmBundle, RequireJSFilter

from werkzeug.local import LocalProxy

# NOTE:
# Here we exclude base JS bundles like jQuery etc. so that there does
# not exist several jQuery instances on the site.
try:
    from flask import current_app
    exclude_js = LocalProxy(
        lambda: current_app.config['THEME_BASE_BUNDLES_EXCLUDE_JS']
    )
except KeyError:
    from invenio_theme.bundles import js as _js
    exclude_js = [_js.contents]


js = NpmBundle(
    'js/workflows/init.js',
    filters=RequireJSFilter(exclude=exclude_js),
    output='gen/workflows.%(version)s.js',
    npm={
        "bootstrap-tagsinput": "git://github.com/inspirehep/bootstrap-tagsinput.git#master",
        "prismjs": "~1.4.1",
        "flightjs": "~1.5.0",
        "hogan.js": "~3.0.2",
        "requirejs-hogan-plugin": "~0.3.1",
    }
)

css = Bundle(
    'node_modules/prismjs/themes/prism.css',
    'node_modules/bootstrap-tagsinput/dist/bootstrap-tagsinput.css',
    'css/workflows/workflows.css',
    filters='scss, cleancss',
    output='gen/workflows.%(version)s.css',
)
