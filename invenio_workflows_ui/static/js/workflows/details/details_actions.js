/*
 * This file is part of Invenio.
 * Copyright (C) 2015 CERN.
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
    'flight'
  ],
  function(
    $,
    flight) {

    "use strict";

    return flight.component(DetailsActions);

    /**
    * .. js:class:: DetailsActions()
    *
    * UI component for handling the buttons for restarting/deleting an object.
    *
    * :param string previewMenuItemSelector: DOM selector for each menu item
    *
    */
    function DetailsActions() {
      this.attributes({
        api_url: function(component) {
            return this.$node.data('api-url');
        },
        objectid: function(component) {
            return this.$node.data('objectid');
        },
      });

      this.handleAction = function(ev, data) {
        this.trigger("return_data_for_exec", {
            "value": data.value,
            "selectedIDs": [this.attr.objectid]
        });
      }

      this.handleDetailsButton = function(ev, data) {
        var alert_message;
        var url;
        var type = "POST";

        if (data.action === "delete") {
          url = this.attr.api_url + this.attr.objectid;
          type = "DELETE";
        } else if (data.action === "resume") {
          url = this.attr.api_url + this.attr.objectid + "/action/resume";
        } else if (data.action === "restart") {
          url = this.attr.api_url + this.attr.objectid + "/action/restart";
        }
        var $this = this;
        var payload = {
          objectid: this.attr.objectid
        };
        if (url !== undefined) {
          $.ajax({
            type: type,
            url: url,
            data: payload,
          }).done(function(data) {
              var message;
              if (data !== undefined && data.hasOwnProperty('result')) {
                 message = data.result;
              } else if (type === "DELETE") {
                 message = "Successfully deleted object with identifier " + $this.attr.objectid;
              } else {
                 message = "Operation completed.";
              }
              $this.trigger(document, "updateAlertMessage", {
                category: 'success',
                message: message
              });
          }).fail(function(jqXHR, textStatus) {
            $this.trigger(document, "updateAlertMessage", {
              category: 'danger',
              message: textStatus
            });
          });
        }
      };

      this.after('initialize', function() {
        this.on(document, "detailsButtonClick", this.handleDetailsButton);
        this.on(document, "execute", this.handleAction);
        console.log("Details actions init");
      });
    }
});
