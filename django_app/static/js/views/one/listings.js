hearo.views.Listings = hearo.View.extend({
    el: "#directory",

    playall: function(){
        $('.play-button').click();
    },

    initialize: function () {
        this.NUM_COLS = 4;
        this._pending = false;

        this.$listContainer = $("#directory");
        this.$list = this.$("#directory-list");

        //limit can be passed from data attribute, limit disables infinitescroll
        if (isNaN(this.$list.attr("data-limit"))) {
            this.limit = false;
        } else {
            this.limit = this.$list.attr("data-limit");
        }

        //initialize masonry
        this.$list.masonry({
            itemSelector: "div.music.listing",
            gutter: 10,
        });

        //setup profile modals
        this._setupArtistDating();

        this.render();

        if (!this.limit) {
            this._setupInfiniteScroll();
        }

    },

    load: function (opts, cb) {
        // magic
        var url = window.location.toString().match(/[^\?]*/)[0];
        var nounSet = false;
        _.forEach(["arists", "albums", "songs", "map"], function (k) {
            if (url.indexOf(k) != -1) {
                nounSet = true;
            }
        });
        // show hide map
        // $('#world-map').vectorMap('get', 'mapObject').updateSize();
        var map_el = $('#world-map');
        var back_el = $('#back-button');
        var noun_count_el = $('#noun-counts');
        var map_obj = map_el.vectorMap('get', 'mapObject');
        if (url.indexOf("map") != -1) {
            noun_count_el.show();
            map_el.show();
            map_obj.updateSize();
            // map back button
            if (map_obj.params.map != 'world_mill_en'){
                back_el.show();
            } else {
                back_el.hide();
            }
            setTimeout(function() {
                try {
                    hearo.listings.$list.masonry();
                } catch(e) { }
            }, 1000);
            console.info('show map');
        } else {
            noun_count_el.hide();
            back_el.hide()
            map_el.hide();
            setTimeout(function() {
                try {
                    hearo.listings.$list.masonry();
                } catch(e) { }
            }, 1000);
            console.info('hide map');
        }
        // needed to fix starting on a page without the map object
        map_obj.reset();
        // fetch nounset
        if (nounSet) {
            $.getJSON(url + ".json" + window.location.search, opts, cb);
        } else {
            if (url.indexOf("profile") != -1) {
                $.getJSON("/all.json" + window.location.search, opts, cb);
                $("#modal-container")
                    .removeClass("loading")
                    .removeClass("open");
                $("#world-map").removeClass("blur");
                $("#directory").removeClass("blur");
                $("#filter-bar").removeClass("blur");
                $("#page").css("position", "static");
            } else {
                $.getJSON(url + "all.json" + window.location.search, opts, cb);
            }
        }
    },

    _lastLoadPayload: undefined,

    render: function (opts) {
        // fix load bug when profile sets height to element height (note: required in
        // multiple places)
        $("body").css({ overflow: "", height: "" });
        // BUG: this gets called twice on subsequent page loads, need to identify
        // whats causing this
        var self = this;

        opts = $.extend(
            {
                append: false,
                ranking: $(
                    $(
                        "#ranking-dropdown li.dropdown-widget__option--selected"
                    )[0]
                ).attr("val"),
                time: $(
                    $("#time-dropdown li.dropdown-widget__option--selected")[0]
                ).attr("val"),
            },
            opts
        );

        if (
            this._lastLoadPayload !== undefined &&
            this._lastLoadPayload.indexOf(window.location.toString()) >= 0
        ) {
            // check if the request payload has changed and update offset
            opts.offset = opts.offset !== undefined ? opts.offset : this.listingsCount();
        }

        if (this.limit) {
            var count = this.limit;
        } else {
            var count = 20;
        }

        opts = _.extend(
            {
                offset: 0,
                count: count,
            },
            opts
        );

        if (typeof hearo.filters != "undefined") {
            opts = _.extend(hearo.filters.musicFilters.toJSON(), opts);
        }

        stringifiedOpts = JSON.stringify(opts) + window.location.toString();

        if (stringifiedOpts === this._lastLoadPayload) {
            self.$list.masonry();
            return; // DRY lol
        }

        this._lastLoadPayload = stringifiedOpts;

        if (!opts.append) {
            //if we aren't appending and masonry is initialized, remove items
            if ($(".music.listing").first().css("position") == "absolute") {
                self.$list.masonry("remove", $("div.music.listing"));
            }
            self.$listContainer.addClass("is-loading");
        }

        // if (typeof addthis_share != "undefined") {
        //     this._updateAddThis();
        // }

        this.load(
            opts,
            function (data) {
                var listings = data.listings;

                if (typeof hearo.nounCounts != "undefined") {
                    hearo.nounCounts.refresh(data.counts);
                }

                if (listings.length === 0) {
                    if (!opts.append) {
                        self.$listContainer.addClass("is-empty");
                    }

                    return self.$listContainer.removeClass("is-loading");
                }

                self.$listContainer.removeClass("is-empty");

                //generate string of new elements
                var html;
                for (var i = listings.length - 1; i >= 0; i--) {
                    html += listings[i];
                }
                var $newElems = $(html);
                self.$list.append($newElems);
                setupLinks();

                self.$list.masonry("appended", $newElems);
                self.$list.masonry();

                var imgLoad = imagesLoaded(self.$list);

                //wait for images to load
                imgLoad.on("always", function (instance) {
                    $("#directory-list").masonry();
                    self._pending = false;
                    self.$listContainer.removeClass("is-loading");
                    console.info("LOADED");
                });

                //broken images seem to break masonry, so if we have any broken imgs settimeout to re-layout masonry
                imgLoad.on("fail", function (instance) {
                    setTimeout(function () {
                        $("#directory-list").masonry();
                    }, 300);
                    setTimeout(function () {
                        $("#directory-list").masonry();
                    }, 700);
                });

                setTimeout(function() {
                    try {
                        hearo.listings.$list.masonry();
                    } catch(e) { }
                }, 1000);


                modalEffectsInit();
            }.bind(this)
        );
    },

    listingsCount: function () {
        return $(".music.listing").length;
    },

    // _updateAddThis: function () {
    //     hearo.utils.addthis.setURL();
    //     if (typeof hearo.filters != "undefined") {
    //         hearo.utils.addthis.setHashtags(hearo.filters.toHashTags());
    //     }
    // },

    _showLoadingIndicator: function () {
        _.defer(function () {
            hearo.utils.scroll.toBottom();
            hearo.listings.$listContainer.addClass("is-loading");
            console.info("LOADING....");
        });
    },

    _pending: false,

    _setupInfiniteScroll: function () {
        var self = this;

        $(window).endlessScroll({
            bottomPixels: 200,
            intervalFrequency: 1000,
            fireOnce: true,
            fireDelay: 200,
            loader: "",
            callback: function () {
                if (self._pending) return;
                self._pending = true;
                self._showLoadingIndicator();
                _.defer(function () {
                    self.render({
                        append: true,
                    });
                });
            },
        });
    },

    _request: false,

    _returnUrl: false,

    _scroll_position: false,

    _artistAjax: function (href, initialize) {
        if (this._request) {
            this._request.abort();
        }

        $("#modal-container #content").html("");

        this._request = $.ajax({
            url: href,
            success: function (data) {
                $("#modal-container #content").replaceWith(
                    $(data).find("#content")
                );
                $("#modal-container").addClass("open");
                if ($(window).width() <= 768) {
                    if ($("div#content.profile").offset().top > 40) {
                        $("div#content.profile").offset({ top: 40 });
                    }
                }
                $("html, body").scrollTop($("#top-gallery").height() + 0);
                setupLinks();
                if (initialize) {
                    hearo.setup["profile"]();
                }

                //update url
                History.pushState(
                    {
                        type: "link", // For google analytics
                        httpReqType: "GET",
                        data: null,
                        samePageRefreshScope: null,
                        requestid: nextRequest(),
                        artistDating: true,
                    },
                    function () {
                        var pathPart = self._returnUrl.split("/")[3].replace("-", " ");
                        var title;

                        if (pathPart != "/") {
                            title = pathPart + ' - Tune.fm';
                        } else {
                            title = "Discover new music on tune.fm";
                        }

                        document.title = title;
                    },
                    href
                );

                // hack to get profile titles correct
                var profile_title =
                    $("#banner-profile-name").html() + " - Tune.fm";
                document.title = profile_title;
            },
        });
    },

    _artistDatingSetup: false,

    _setupArtistDating: function () {
        var self = this;

        //prevent attachment of multiple event handlers
        if (this._artistDatingSetup) {
            return false;
        }

        $(document).on("click", "#primary-content a.profile-ajax", function (
            e
        ) {
            e.preventDefault();
            var href = $(this).attr("href");

            $("#modal-container").addClass("loading");
            self._artistAjax(href, true);
        });

        $(document).on("click", "#directory-list .profile-ajax", function (e) {
            e.preventDefault();

            self._returnUrl = History.getState().url;
            self._scroll_position = $(document).scrollTop();
            var href = $(this).attr("href");

            //mark current profile
            $(".music.listing.active").removeClass("active");
            $(this).parents(".music.listing").addClass("active");

            $("#modal-container").addClass("loading");
            $("#world-map").addClass("blur");
            $("#directory").addClass("blur");
            $(".filter-bar").addClass("blur");
            self._artistAjax(href, true);
        });

        $(document).on("click", "#modal-backdrop, .modal-quit", function () {
            $("body").css({ overflow: "", height: "" });
            self._pending = false;
            $("#modal-container").removeClass("loading").removeClass("open");
            $("#world-map").removeClass("blur");
            $("#directory").removeClass("blur");
            $(".filter-bar").removeClass("blur");
            $("#page").css("position", "static");

            if (self._scroll_position) {
                $("html, body").scrollTop(self._scroll_position);
            }

            //cancel ajax request if exist
            if (self._request) {
                self._request.abort();
            }
            //update url
            History.pushState(
                {
                    type: "link", // For google analytics
                    httpReqType: "GET",
                    data: null,
                    samePageRefreshScope: null,
                    requestid: nextRequest(),
                    artistDating: true,
                },
                null,
                self._returnUrl
            );
        });

        $(document).on("click", ".modal-left-arrow", function () {
            self._updateArtistModal(true);
        });

        $(document).on("click", ".modal-right-arrow", function () {
            self._updateArtistModal(false);
        });

        //left-right keyboard navigation
        $("body").keydown(function (e) {
            //if($('#modal-container').hasClass('loading') || $('#modal-container').hasClass('open')){
            if ($("#modal-container").hasClass("open")) {
                if (e.keyCode == 37) {
                    // left
                    self._updateArtistModal(true);
                } else if (e.keyCode == 39) {
                    // right
                    self._updateArtistModal(false);
                }
            }
        });

        this._artistDatingSetup = true;
    },

    _updateArtistModal: function (prev) {
        var active = $(".music.listing.active");
        if (prev) {
            var elem = active.prev(".music.listing");
        } else {
            var elem = active.next(".music.listing");
        }
        if (elem.length) {
            var href = elem.find(".profile-ajax.ajax").attr("href");
            active.removeClass("active");
            elem.addClass("active");
            $("#modal-container").addClass("loading");
            $("#modal-container #content").html("");
            this._artistAjax(href, false);
        }
    },
});
