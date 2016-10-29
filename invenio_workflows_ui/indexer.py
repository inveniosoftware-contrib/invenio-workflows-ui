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

"""Indexer overrides workflows UI interface."""

from __future__ import absolute_import, print_function

import pytz

from invenio_indexer.api import RecordIndexer


class WorkflowIndexer(RecordIndexer):
    """Special indexer for workflow objects."""

    @staticmethod
    def _prepare_record(record, index, doc_type):
        """Prepare the workflow object record for ES."""
        data = record.dumps()
        if record.model.created.tzinfo:
            data['_created'] = record.model.created.isoformat()
        else:
            data['_created'] = (
                pytz.utc.localize(record.model.created).isoformat()
                if record.model.created else None
            )
        if record.model.modified.tzinfo:
            data['_updated'] = record.model.modified.isoformat()
        else:
            data['_updated'] = (
                pytz.utc.localize(record.model.modified).isoformat()
                if record.model.modified else None
            )
        return data

    def index(self, record):
        """Index a record without version.

        NOTE: Can be removed when invenio-workflows model use versioning.

        :param record: Record instance.
        """
        index, doc_type = self.record_to_index(record)
        if not index or not doc_type:
            return
        return self.client.index(
            id=str(record.id),
            index=index,
            doc_type=doc_type,
            body=self._prepare_record(record, index, doc_type),
        )
