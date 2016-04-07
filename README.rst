..
    This file is part of Invenio.
    Copyright (C) 2016 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.

======================
 invenio-workflows-ui
======================

.. image:: https://img.shields.io/travis/inveniosoftware/invenio-workflows-ui.svg
        :target: https://travis-ci.org/inveniosoftware/invenio-workflows-ui

.. image:: https://img.shields.io/coveralls/inveniosoftware/invenio-workflows-ui.svg
        :target: https://coveralls.io/r/inveniosoftware/invenio-workflows-ui

.. image:: https://img.shields.io/github/tag/inveniosoftware/invenio-workflows-ui.svg
        :target: https://github.com/inveniosoftware/invenio-workflows-ui/releases

.. image:: https://img.shields.io/pypi/dm/invenio-workflows-ui.svg
        :target: https://pypi.python.org/pypi/invenio-workflows-ui

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio-workflows-ui.svg
        :target: https://github.com/inveniosoftware/invenio-workflows-ui/blob/master/LICENSE


Invenio module which acts as a UI layer for invenio-workflows.

*This is an experimental developer preview release.*

* Free software: GPLv2 license
* Documentation: https://pythonhosted.org/invenio-workflows-ui/


Configuration
=============

In order to build assets correctly, you need to modify your instance
``settings.js`` and add the following to the list of ``paths``:

.. code-block: javascript

    hgn: "node_modules/requirejs-hogan-plugin/hgn",
    hogan: "node_modules/hogan.js/web/builds/3.0.2/hogan-3.0.2.amd",
    text: "node_modules/requirejs-hogan-plugin/text",
    flight: "node_modules/flightjs/build/flight"
