/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2014-2017  Hybird

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*******************************************************************************/

(function($) {
"use strict";

creme.geolocation = creme.geolocation || {};

// TODO: rename PersonsBrick etc..
// TODO: rename CSS classes 'block-geoaddress-*' into '.geolocation-brick-*'

creme.geolocation.PersonsBlock = creme.component.Component.sub({
    STATUS_LABELS: {
        0: gettext("Not localized"),
        1: gettext("Manual location"),
        2: gettext("Partially matching location"),
        3: ''
    },

//    _init_: function(block, addresses)
    _init_: function(block, addresses, set_address_info_url) {
        if (set_address_info_url === undefined) {
            console.warn('creme.geolocation.PersonsBlock(): hard-coded "set_address_info_url" is deprecated ; give it as parameter.');
        }

        var self = this;

        this._block = block;
        this._addresses = addresses;

//        var controller = this._controller = new creme.geolocation.GoogleMapController();
        var controller = this._controller = new creme.geolocation.GoogleMapController(set_address_info_url);
        var container = $('.block-geoaddress-canvas', block);

        if (container.length) {
            controller.enableMap(container.get(0));
        }

        $('.block-geoaddress-item .block-geoaddress-reset', block).click(this._onRefreshLocation.bind(this));

        addresses.forEach(this._geocodeAddress.bind(this));

        controller.on('save-location', function(event, address, marker, status) {
            self._showPosition(address.id, marker);
            self._showStatus(address.id, status);

            block.trigger('block-geoaddress-location', [address, marker]);
        });

        $('.block-geoaddress-item input[type="checkbox"]', block).each(function() {
                                                                      self._toggleLocation($(this).val(), $(this).is(':checked'));
                                                                  })
                                                                 .change(this._onToggleLocation.bind(this));

        block.bind('creme-table-collapse', function(e, status) {
            if (status.action === 'show') {
                controller.resize();
                controller.adjustMap();
            }
        });
    },

    _geocodeAddress: function(address) {
        var self = this;
        var controller = this._controller;

        if (controller.isAddressLocated(address)) {
            controller.marker_manager.Marker({
                address: address,
                draggable: true,
                visible: false
            });
        } else {
            controller.findLocation(address, {
                draggable: true,
                done: function(marker) {
                    controller.marker_manager.hideAll();
                },
                fail: function(data) {
                    self._showStatus(address.id, data);
                }
            });
        }
    },

    addressItem: function(address_id) {
        return $('.block-geoaddress-item[data-addressid="' + address_id + '"]', this._block);
    },

    _showStatus: function(address_id, status) {
        var item = this.addressItem(address_id);
        var is_complete = (status === creme.geolocation.LocationStatus.COMPLETE);

        item.find('.block-geoaddress-status').html(this.STATUS_LABELS[status]);
        item.find('.block-geoaddress-action').toggleClass('block-geoaddress-iscomplete', is_complete);
    },

    _showPosition: function(address_id, marker) {
        var content = '';

        if (!Object.isEmpty(marker)) {
            content = '%3.6f, %3.6f'.format(marker.position.lat(),
                                            marker.position.lng());
        }

        // result.formatted_address
        this.addressItem(address_id).find('.block-geoaddress-position').html(content);
    },

    _toggleLocation: function(address_id, status) {
        this._controller.marker_manager.toggle(address_id, status);
        this.addressItem(address_id).toggleClass('item-selected', status);
    },

    _onRefreshLocation: function(event) {
        var self       = this;
        var controller = this._controller;

        var address_id = parseInt($(event.target).attr('data-addressid'));
        var marker     = controller.getMarker(address_id);

        if (marker) {
            this._controller.findLocation(marker.address, {
                                 done: function(marker, result, status) {
                                     controller.adjustMap();
                                 },
                                 fail: function(status) {
                                     self._showPosition(address_id);
                                     self._showStatus(address_id, status);
                                 }
                             });
        }
    },

    _onToggleLocation: function(event) {
        this._toggleLocation($(event.target).val(), $(event.target).is(':checked'));
    }
});


creme.geolocation.AddressesBlock = creme.component.Component.sub({
//    _init_: function(block) {
    _init_: function(block, addresses_url, set_address_info_url) {
        if (addresses_url === undefined) {
            console.warn('creme.geolocation.AddressesBlock(): hard-coded "addresses_url" is deprecated ; give it as the second parameter.');
            this.addresses_url = '/geolocation/get_addresses/';
        } else {
            this.addresses_url = addresses_url;
        }

        if (set_address_info_url === undefined) {
            console.warn('creme.geolocation.AddressesBlock(): hard-coded "set_address_info_url" is deprecated ; give it as the third parameter.');
        }

//        var controller = this._controller = new creme.geolocation.GoogleMapController();
        var controller = this._controller = new creme.geolocation.GoogleMapController(set_address_info_url);
        var filterSelector = this._filterSelector = $('.block-geoaddress-filter', block);
        var container = $('.block-geoaddress-canvas', block);

        filterSelector.change(this._onFilterChange.bind(this));

        if (container.length) {
            controller.enableMap(container.get(0));
        }

        this._updateFilter(filterSelector.val());

        block.bind('creme-table-collapse', function(e, status) {
            if (status.action === 'show') {
                controller.resize();
                controller.adjustMap();
            }
        });
    },

    _queryAddresses: function(filter, listeners) {
        var self = this;
        var controller = this._controller;
        var updateAddress = this._updateAddress.bind(this);

        var url = this.addresses_url;
        if (filter) {
            url = url + '?id=' + filter;
        }

//        creme.ajax.query('/geolocation/get_addresses_from_filter/%s'.format(filter))
        creme.ajax.query(url)
                  .converter(JSON.parse)
                  .onDone(function(event, data) {
                      data.addresses.forEach(updateAddress);
                      controller.adjustMap();
                      self._showCount(data.addresses.length);
                   })
                  .onFail(function() {
                      controller.adjustMap();
                      self._showCount(0);
                  })
                  .on(listeners || {}).get();
    },

    _updateAddress: function(address) {
        var controller = this._controller;
        var marker = controller.marker_manager.get(address.id);

        if (!marker) {
            if (controller.isAddressLocated(address)) {
                controller.marker_manager.Marker({
                    address:   address,
                    draggable: false,
                    redirect:  address.url
                });
            }
        } else {
            marker.setVisible(true);
        }
    },

    _onFilterChange: function(event) {
        var controller = this._controller;
        var filter = $(event.target).val();

        controller.marker_manager.hideAll();

        this._updateFilter(filter, {
                 fail: function() {
                     $(event.target).val('');
                 }
             });
    },

    _updateFilter: function(filter, listeners) {
        if (filter) {
            this._queryAddresses(filter, listeners);
        } else {
            this._controller.adjustMap();
            this._showCount(0);
        }
    },

    _showCount: function(count) {
        var content = !count ? gettext('No address from') : ngettext('%0$d address from', '%0$d addresses from', count).format(count);
        $('.block-geoaddress-counter', this._block).html(content);
    }
});


creme.geolocation.PersonsNeighborhoodBlock = creme.component.Component.sub({
//    _init_: function(block, radius) {
    _init_: function(block, radius, neighbours_url, set_address_info_url) {
        if (neighbours_url === undefined) {
            console.warn('creme.geolocation.PersonsNeighborhoodBlock(): hard-coded "neighbours_url" is deprecated ; give it as the third parameter.');
            this.neighbours_url = '/geolocation/get_neighbours/';
        } else {
            this.neighbours_url = neighbours_url;
        }

        if (set_address_info_url === undefined) {
            console.warn('creme.geolocation.PersonsNeighborhoodBlock(): hard-coded "set_address_info_url" is deprecated ; give it as the fourth parameter.');
        }

//        var controller = this._controller = new creme.geolocation.GoogleMapController();
        var controller = this._controller = new creme.geolocation.GoogleMapController(set_address_info_url);
        this._radius = radius;
        this._block = block;

        var container = $('.block-geoaddress-canvas', block);

        if (container.length) {
            controller.enableMap(container.get(0));
        }

        this._sourceSelector = $('.block-geoaddress-source', block).change(this._onChange.bind(this));
        this._filterSelector = $('.block-geoaddress-filter', block).change(this._onChange.bind(this));

        this._onChange();

        block.bind('creme-table-collapse', function(e, status) {
            if (status.action === 'show') {
                controller.resize();
                controller.shape_manager.adjustMap('NeighbourhoodCircle');
            }
        });
    },

    _queryNeighbours: function(address, filter) {
        if (!address) {
            this._controller.adjustMap();
            return;
        }

        var updateNeighbours = this._updateNeighbours.bind(this);

        var url = this.neighbours_url + '?address_id=' + address;
        if (filter) {
            url = url + '&filter_id=' + filter;
        }

//        creme.ajax.query('/geolocation/get_neighbours/%s/%s'.format(address, filter || ''))
        creme.ajax.query(url)
                  .converter(JSON.parse)
                  .onDone(function(event, data) {
                       updateNeighbours(data.source_address, data.addresses);
                   })
                  .onFail(function() {
                       updateNeighbours(address, []);
                   })
                  .get();
    },

    _clearNeighbours: function() {
        var controller = this._controller;
        controller.marker_manager.hideAll();

        if (controller.shape_manager.get('NeighbourhoodCircle')) {
            controller.shape_manager.unregister('NeighbourhoodCircle');
        }
    },

    /* global google */
    _updateMarker: function(address, options) {
        if (Object.isNone(address)) {
            return;
        }

        var controller = this._controller;
        var marker = controller.marker_manager.get(address.id);

        if (controller.isAddressLocated(address)) {
            if (marker) {
                marker.setPosition(new google.maps.LatLng(address.latitude, address.longitude));
            } else {
                options = $.extend({
                    address: address,
                    draggable: false
                }, options || {});

                marker = controller.marker_manager.Marker(options);
            }

            marker.setVisible(true);
        }

        return marker;
    },

    /* global google */
    _updateNeighbours: function(source, addresses) {
        this._clearNeighbours();

        var controller = this._controller;
        var sourceMarker = this._updateMarker(source, {
                                                  icon: {
                                                      path: google.maps.SymbolPath.CIRCLE,
                                                      scale: 5
                                                  }
                                              });

        if (!sourceMarker) {
            return this;
        }

        controller.shape_manager.register('NeighbourhoodCircle',
            new google.maps.Circle({
                strokeColor: '#dea29b',
                strokeOpacity: 0.9,
                strokeWeight: 2,
                fillColor: '#dea29b',
                fillOpacity: 0.40,
                map: controller.map,
                center: sourceMarker.position,
                radius: this._radius
        }));

        this._showCount(addresses.length);

        var addressMarker = this._updateMarker.bind(this);

        addresses.forEach(function(address) {
            addressMarker(address, {redirect: address.url});
        });

        controller.shape_manager.adjustMap('NeighbourhoodCircle');
    },

    sourcePosition: function(address, position) {
        var mark = this._controller.getMarker(address.id);

        if (mark) {
            mark.setPosition(position);

            if (this._sourceSelector.val() === '' + address.id) {
                this._queryNeighbours(this._sourceSelector.val(), this._filterSelector.val());
            }
        }
    },

    _onChange: function(event) {
        this._queryNeighbours(this._sourceSelector.val(), this._filterSelector.val());
    },

    _showCount: function(count) {
        var counter = !count ? gettext('None of') : ngettext('%0$d of', '%0$d of', count).format(count);
        $('.block-geoaddress-counter', this._block).html(counter);
    }
});

}(jQuery));