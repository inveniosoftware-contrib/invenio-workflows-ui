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
    'flight/lib/component'
  ],
  function(
    $,
    defineComponent) {

    "use strict";

    return defineComponent(HoldingPenUrlUpdater);

    function HoldingPenUrlUpdater() {

      this.attributes({
        and: ' AND ',
        pathSuffix: 'holdingpen/list',
        listSuffix: 'list/'
      });

      this.updateUrlFromTags = function(ev, data) {
        var len = data.tags.length;
        console.log("Tags length: " + len);

        // Different states depending on the number of tags
        switch(len) {
          case 0:
            this.replaceHistoryUrl('.'); // history API accepts UNIX-like relative paths
            break;
          case 1:
            this.replaceHistoryUrl(data.tags[0]);
            break;
          default:
            var url_state = data.tags[0];
            for (var i = 1; i < len; i++)
              url_state += this.attr.and + data.tags[i];
            this.replaceHistoryUrl(url_state);
        }
      };

      this.replaceHistoryUrl = function(url_state) {
        // Replace certain characters that may cause encoding problems
        url_state = url_state
          .replace(':', '%3A')
          .replace(' ', '%20');

        // Check if url ends with /list, to avoid problems with pushState
        if (this.endsWith(window.location.pathname, this.attr.pathSuffix)) {
          history.replaceState({}, '', this.attr.listSuffix + url_state);
        } else {
          history.replaceState({}, '', url_state);
        }
      };

      this.endsWith = function(str, suffix) {
        return str.indexOf(suffix, str.length - suffix.length) !== -1;
      };

      this.after('initialize', function() {
        this.on(document, "update_url", this.updateUrlFromTags);
        console.log("Url Updater init");
      });
    }
  });
