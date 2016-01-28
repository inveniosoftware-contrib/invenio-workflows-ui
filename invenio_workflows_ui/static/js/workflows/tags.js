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
    'jquery',
    'flight',
    'node_modules/selectize/dist/js/selectize'
  ],
  function(
    $,
    flight,
    selectize) {

    'use strict';

    return flight.component(WorkflowsUITags);

    /**
    * .. js:class:: WorkflowsUITags()
    *
    * Component for handling the filter/search available through interface.
    *
    * :param Array tags: list of tags to add from the beginning.
    *
    */
    function WorkflowsUITags() {

      this.attributes({
        tags: []
      });

      /* Event handler for dropdown selection
       *
       * `this` is the context of this component
       */
      this.addTagFromMenu = function(ev, data) {
        var that = this;
        var items = this.getItems();

        if (data.prefix) {
            var tags_to_remove = $.grep(items, function(item, index) {
              return item.slice(0, data.prefix.length) == data.prefix;
            });
            $.each(tags_to_remove, function(index, item) {
              that.$node[0].selectize.removeItem(item);
            })
        }
        this.$node[0].selectize.createItem(data.value);
      };

      this.getItems = function() {
          return this.$node[0].selectize.items
      };


      this.addTagFromFreetext = function(ev) {
        // ev.item is the freeinput text
        if (ev.item.length != 0){
          ev.item = {text: ev.item, value: ev.item};
          // event.cancel: set to true to prevent the item getting added
          ev.cancel = false;
        }
      };

      /* Event handler for manual trigger of updateing tags
       *
       * `this` is the context of the component
       */
      this.componentTagsUpdate = function() {
        var payload = {};
        payload.search = this.$node[0].selectize.$input.val();

        $(document).trigger("reloadWorkflowsUITable", payload);
        $(document).trigger("update_url", payload);
      };

      /* Event handler for selectize onItemAdd/onItemRemove
       *
       * `this` is the context of the selectize instance
       */
      this.onTagsUpdate = function(ev, data) {
        var payload = {};
        payload.search = this.$input.val();

        $(document).trigger("reloadWorkflowsUITable", payload);
        $(document).trigger("update_url", payload);
      };

      this.after('initialize', function() {
        this.on(document, "addTagFromMenu", this.addTagFromMenu);
        this.on(document, "updateTags", this.componentTagsUpdate);

        this.$node.selectize({
            plugins: ['restore_on_backspace', 'remove_button'],
            delimiter: ' AND ',
            persist: false,
            create: function(input) {
                return {
                    value: input,
                    text: input
                }
            },
            onChange: this.onTagsUpdate,
            onInitialize: this.onTagsUpdate,
        });


        // Add any existing tags
        // var that = this;
        // this.attr.tags.map(function(item) {
        //  that.$node.tagsinput('add', item);
        // });

      });
    }
});
