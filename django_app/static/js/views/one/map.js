codeOffset = 0;
COUNTRIES_MINIMIZE_DRILL_DOWN = [
    "AR",
    "AT",
    "AU",
    "BE",
    "CA",
    "CN",
    "CO",
    "DE",
    "DK",
    "ES",
    "FR",
    "GB",
    "IN",
    "IT",
    "NL",
    "NO",
    "NZ",
    "PL",
    "PT",
    "RU",
    "SE",
    "TH",
    "VE",
    "ZA",
];

function loadMap(name, self) {
    var mapObject = self.$el.vectorMap("get", "mapObject");
    var map_name = mapObject.params.map;
    if (name != "world_mill_en") {
        $("#back-button").show();
        $("#back-button").data("mapdata", self);
    } else {
        $("#back-button").hide();
        $("#back-button").data("mapdata", self);
    }
    try {
        mapObject.remove();
    } catch (err) {}

    vectorMap(name, self);
}

function switchMap(code, self) {
    if (!self) {
        // assign mapdata from previous map
        self = $("#back-button").data("mapdata");
        // HACK: needs to be set to get markers to work
        codeOffset = codeOffset + hearo.directory.coords.length;
    }

    if (!isNaN(parseInt(code))) {
        // HACK: convert to int to detect if a county is being clicked
        // in which case we might not necessarily want to go back to world
        return;
    } else if (code.indexOf("US-") > -1) {
        name = code.toLowerCase() + "_lcc_en";
        url =
            "/public/lib/jquery/jvectormap/us/jquery-jvectormap-data-" +
            code.toLowerCase() +
            "-lcc-en.js";
    } else if (code.indexOf("-") > -1) {
        // Dont support regions within other countries except for US
        return;
    } else {
        name = code.toLowerCase() + "_mill";
        url =
            "/public/lib/jquery/jvectormap/jquery-jvectormap-" +
            code.toLowerCase() +
            "-mill.js";
    }

    //console.info('code=', code, 'name=', name, 'url=', url);

    $.ajax({
        url: url,
        dataType: "script",
        success: function () {
            loadMap(name, self);
        },
        error: function () {
            name = "world_mill_en";
            loadMap(name, self);
        },
    });
}

function vectorMap(map, self) {
    self.$el.vectorMap({
        map: map,
        zoomButtons: false,
        // zoomOnScroll: false,
        // map: 'us_lcc_en',
        focusOn: {
            x: 0.5,
            y: 0.5,
            scale: 1,
        },
        markers: self.markers,
        //  selectedRegions: selected_region,
        onRegionClick: function (e, code) {
            // console.info('ONREGIONCLICK ---------------->', e, code);
            // allow only if the following conditions are met
            if (
                isNaN(code) && // skip US state counties (all numeric)
                !new RegExp(COUNTRIES_MINIMIZE_DRILL_DOWN.join("-|")).test(code)
            ) {
                self._toggleCountry(code);
                switchMap(code, self);
            }
        },
        onRegionOver: function (e, code) {
            if (typeof hearo.directory.countries[code] != "undefined") {
                self.updateCaption(
                    hearo.directory.countries[code][0],
                    hearo.directory.countries[code][1]
                );
                if (/(iPad|iPhone|iPod)/g.test(navigator.userAgent)) {
                    self._toggleCountry(code);
                }
            }
        },
        onRegionOut: function (e, code) {
            self.updateCaption();
        },
        onRegionLabelShow: function (e, el, code) {
            if (/(iPad|iPhone|iPod)/g.test(navigator.userAgent)) {
                self._toggleCountry(code);
            }
        },
        onMarkerClick: function (e, code) {
            //console.info('markerclick=', code);
            self._toggleCoordinate(
                hearo.directory.coords[code - codeOffset].name
            );
        },
        onMarkerOver: function (e, code) {
            try {
                self.updateCaption(
                    hearo.directory.coords[code - codeOffset].count,
                    hearo.directory.coords[code - codeOffset].name
                );
                if (/(iPad|iPhone|iPod)/g.test(navigator.userAgent)) {
                    self._toggleCountry(code);
                }
            } catch (e) {
                //debugger;
            }
        },
        onMarkerOut: function (e, code) {
            self.updateCaption();
        },
        regionsSelectable: true,
        markersSelectable: true,
        regionsSelectableOne: true,
        markersSelectableOne: true,
        backgroundColor: "#2B5D8F",
        markerStyle: {
            initial: {
                fill: "#CCFFE6",
                stroke: "#00934a",
                "fill-opacity": 1,
                "stroke-width": 0.8,
                "stroke-opacity": 1,
                r: 3,
            },
            hover: {
                r: 6,
                fill: "#FF608A",
                stroke: "#00934a",
                "stroke-width": 0.8,
            },
            selected: {
                fill: "#FF608A",
            },
            selectedHover: {},
        },
        regionStyle: {
            initial: {
                fill: "#1f8a70",
                "fill-opacity": 1,
                stroke: "#1ABB8A",
                "stroke-width": 0.4,
                "stroke-opacity": 0.6,
            },
            hover: {
                "fill-opacity": 0.8,
            },
            selected: {
                fill: "#3FC0A1",
            },
            selectedHover: {},
        },
    });
}

hearo.views.Map = hearo.View.extend({
    el: "#world-map",
    markers: [],
    initialize: function () {
        this._buildLocations();
        //var selected_region = hearo.filters.get('location');
        hearo.directory.coords.forEach(
            function (coord) {
                this.markers.push({
                    latLng: [coord.lat, coord.lng],
                    name: coord.name,
                });
                //this.drawMapLight(coord);
            }.bind(this)
        );

        var self = this;

        vectorMap("world_mill_en", self);
    },
    _buildLocations: function () {
        var countries = hearo.directory.countries,
            coords = hearo.directory.coords,
            global = countries.global;
        this.locations = {};
        // Build the frontend location autosuggestion list

        for (var key in countries) {
            var x = countries[key];
            this.locations[x[1]] = key;
        }

        coords.forEach(
            function (x) {
                this.locations[x.name] = x.lat + "," + x.lng;
            }.bind(this)
        );

        this.locationKeys = Object.keys(this.locations).filter(function (key) {
            return key !== undefined;
        });
    },

    updateCaption: function (count, caption) {
        if (typeof count === "undefined") {
            var count = hearo.directory.countries.global[0];
        }

        if (typeof caption === "undefined") {
            var caption = $("#main-caption-location").data("default");
        }

        $("#count-number").html(count);
        $("#main-caption-location").html("in " + caption);
    },

    _toggleCountry: function (location) {
        // Takes in a DOM elem
        try {
            hearo.filters.setLocation(hearo.directory.countries[location][1]);
        } catch (e) {
            var mapObject = this.$el.vectorMap("get", "mapObject");
            var name = mapObject.mapData.paths[location.toUpperCase()].name;
            hearo.filters.setLocation(name);
        }
    },

    _toggleCoordinate: function (name) {
        // Takes in a string
        hearo.filters.setLocation(name);
    },
});
