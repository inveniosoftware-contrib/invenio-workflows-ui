# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
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


"""Responsify tests."""

from __future__ import absolute_import, division, print_function

from datetime import datetime
from mock import MagicMock

from invenio_workflows_ui.serializers.response import workflow_responsify


class TestSerializer(object):
    """Test serializer."""

    def serialize(self, obj, **kwargs):
        """Dummy method."""
        return "{}".format(obj.title)


def test_workflow_responsify(app):
    """Test responsify."""
    with app.app_context():
        rec_serializer = workflow_responsify(
            TestSerializer(), 'application/json')
        rec = MagicMock(
            model=MagicMock(modified=datetime.now()), title='Jessica Jones')
        resp = rec_serializer(rec)

        assert resp.status_code == 200
        assert resp.content_type == 'application/json'
        assert resp.get_data(as_text=True) == "Jessica Jones"
        assert 'Etag' in resp.headers
