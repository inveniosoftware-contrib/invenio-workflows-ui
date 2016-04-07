/*
 * This file is part of Invenio.
 * Copyright (C) 2014, 2015 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

define(
  [
     "js/workflows/common",
     "js/workflows/details_actions",
     "js/workflows/details_actions_buttons",
     "js/workflows/details_page"
  ],
  function(
    WorkflowsUICommon,
    DetailsActions,
    DetailsActionsButtons,
    DetailsPage) {

    "use strict";

    function initialize(context) {
      WorkflowsUICommon.attachTo(document);
      DetailsActions.attachTo(document, {
        restart_url: context.restart_url,
        delete_url: context.delete_url,
        id_object: context.id_object
      });
      DetailsActionsButtons.attachTo(document);
      DetailsPage.attachTo(document, {
        next_page_url: context.next_page_url,
        previous_page_url: context.previous_page_url,
        main_list_url: context.main_list_url
      });
    }

    return initialize;
  }
);
