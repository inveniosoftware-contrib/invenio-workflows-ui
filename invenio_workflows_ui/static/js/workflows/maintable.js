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
    "js/workflows/ui",
    "js/workflows/pagination",
    "js/workflows/perpage_menu",
    "js/workflows/sort_menu",
    "js/workflows/tags",
    "js/workflows/tags_menu",
    "js/workflows/selection",
    "js/workflows/url_updater"
  ],
  function(
    WorkflowsUICommon,
    WorkflowsUI,
    WorkflowsUIPagination,
    WorkflowsUIPerPage,
    WorkflowsUISort,
    WorkflowsUITags,
    WorkflowsUITagsMenu,
    WorkflowsUISelection,
    WorkflowsUIUrlUpdater) {

    "use strict";

    WorkflowsUICommon.attachTo(document);
    WorkflowsUI.attachTo(document);
    WorkflowsUIPagination.attachTo("#hp-pagination");
    WorkflowsUIPerPage.attachTo("#hp-perpage-menu");
    WorkflowsUISort.attachTo("#hp-sort-menu");
    WorkflowsUITags.attachTo("#search-input");
    WorkflowsUITagsMenu.attachTo("#hp-tags-menu", {
      menuitemSelector: "#hp-tags-menu a",
      valuePrefix: "_workflow.status:"
    });
    WorkflowsUITagsMenu.attachTo("#hp-type-menu", {
      menuitemSelector: "#hp-type-menu a",
      valuePrefix: "_workflow.data_type:"
    });
    WorkflowsUITagsMenu.attachTo("#hp-name-menu", {
      menuitemSelector: "#hp-name-menu a",
      valuePrefix: "_workflow.workflow_name:"
    });
    WorkflowsUISelection.attachTo(document);
    WorkflowsUIUrlUpdater.attachTo(document, {
      urlPrefix: $('#workflows-ui-init').data('list-url')
    });

    $(document).trigger("reloadWorkflowsUITable");
  }
);
