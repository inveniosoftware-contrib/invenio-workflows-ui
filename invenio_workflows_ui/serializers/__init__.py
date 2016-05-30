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

"""Record serialization."""

from __future__ import absolute_import, print_function

import json

from .response import (
    workflow_responsify,
    search_responsify,
    action_responsify,
    file_responsify
)
from .json import JSONSerializer

json_v1 = JSONSerializer()
json_serializer = workflow_responsify(json_v1, 'application/json')
json_search_serializer = search_responsify(json_v1, 'application/json')
json_action_serializer = action_responsify(json_v1, 'application/json')
json_file_serializer = file_responsify(json_v1, 'application/json')
