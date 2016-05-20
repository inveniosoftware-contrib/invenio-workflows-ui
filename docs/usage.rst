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


Usage
=====

In order to integrate your existing "invenio-workflows" with the user interface of
`invenio-workflows-ui`, you need to configure your search (elasticsearch) mappings for the
data structures in your workflows, add some additional properties to the workflow definitions
and configure the UI and REST endpoints.

As an example lets add integration for incoming books, videos and article metadata. We will use `invenio-workflows-ui`
as an interface to view, and accept or reject incoming items.


Setting up search indices
-------------------------

First we need to setup search indexes with the appropriate data model mappings. Similar to the integration of
`invenio-search` and `invenio-records`. We add indexes with common alias "incoming" and several different data types underneath:

1. Create a folder called `mappings` somewhere in your overlay with your search mapping configuration, like this structure:

.. code-block:: bash

    mappings/
        __init__.py
        incoming/
            book.json
            video.json
            article.json


Note, for `invenio-workflows-ui` to work correctly, your search mappings should define the extra fields
specified under `invenio_workflows_ui/mappings/workflows/record.json`. This is used for filtering on status,
created/modified date. Basically fields added under `_workflow.*`.


2. Add the new mappings to the `invenio_search.mappings` entry-point, if necessary:

.. code-block:: python

    'invenio_search.mappings': [
        'incoming = youroverlay.mappings',
    ]


3. `pip install` your overlay again and recreate indexes:

.. code-block:: bash

    pip install .
    youroverlay index init


Adding configuration and workflow properties
--------------------------------------------

Now we are ready to setup the configuration and extra properties in the workflow definitions.

In your workflow definitions, make sure you add the ``data_type`` attribute:

.. code-block:: python

    class MyBookWorkflow(object):
        data_type = "book"
        workflow = [a, b, c]


Then map the `data_type` value as the key to the search index and search type.

.. code-block:: python

    WORKFLOWS_UI_DATA_TYPES = dict(
        book=dict(
            search_index='incoming-book',
            search_type='book',
        ),
        video=dict(
            search_index='incoming-video',
            search_type='video',
        ),
        article=dict(
            search_index='incoming-article',
            search_type='article',
        ),
    )


Configuring the API
-------------------

Finally, you need to setup your UI and REST API endpoint configuration. We will have a UI endpoint called `/incoming` under the
root URL, e.g. http://localhost:5000/incoming

Then the REST API will be available under http://localhost:5000/api/incoming

.. code-block:: python

    WORKFLOWS_UI_URL = "/incoming"
    WORKFLOWS_UI_API_URL = "/api/incoming/"
    WORKFLOWS_UI_REST_ENDPOINT = dict(
        workflow_object_serializers={
            'application/json': ('invenio_workflows_ui.serializers'
                                 ':json_serializer'),
        },
        search_serializers={
            'application/json': ('invenio_workflows_ui.serializers'
                                 ':json_search_serializer'),
        },
        action_serializers={
            'application/json': ('invenio_workflows_ui.serializers'
                                 ':json_action_serializer'),
        },
        bulk_action_serializers={
            'application/json': ('invenio_workflows_ui.serializers'
                                 ':json_action_serializer'),
        },
        list_route='/incoming/',
        item_route='/incoming/<object_id>',
        search_index="incoming",   # <- main search alias for all "incoming" indices
        default_media_type='application/json',
        max_result_window=10000,
    )


Note that the ``search_index`` value should be the same as the folder name containing the mappings for invenio-workflows-ui, e.g. "incoming".


Known Issues
============

Errors while building assets
----------------------------

In order to build assets correctly, you need to modify your instance
``settings.js`` file and add the following to the list of ``paths``:

.. code-block:: javascript

    {
      hgn: "node_modules/requirejs-hogan-plugin/hgn",
      hogan: "node_modules/hogan.js/web/builds/3.0.2/hogan-3.0.2.amd",
      text: "node_modules/requirejs-hogan-plugin/text",
      flight: "node_modules/flightjs/build/flight"
    }


If you use `invenio-theme`, you may need to adjust the settings.js file contained within
the module. Or, alternatively, roll your own bundle with an updated `settings.js` file.
