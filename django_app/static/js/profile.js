/*global
  hearo,
  */

(function () {
    var setup = function () {
        hearo.setup.reviews.initialize();

        // Profile primary key
        var pk = parseInt($("#profile").attr("pk"), 10);

        hearo.lightbox.queue = [];

        modalEffectsInit();

        var $el = $("#profile");
        var elheight = $el.height();
        var windowheight = $(window).height();
        var hdiff = elheight - windowheight;

        // 100px beyond element (fix for listings)
        // HACK: this can also be put in the listings module
        if ($("#directory").length) {
            window.hearo.listings._pending = true;
            $("body").css({
                height: $el.position().top + $el.height() + 200,
                overflow: "hidden",
            });
            // block listings from attempting to load endless scroll
        }

        // Fand content tab actionz
        $("ul#fand-content-tabs li").each(function () {
            var $self = $(this);
            $self.click(function () {
                $self.siblings().each(function () {
                    this.setAttribute("selected", "false");
                });
                this.setAttribute("selected", "true");
                $("#scrollbar-screen-fand-content > div").hide();
                $($self.attr("opens")).show();
            });
        });

        // Update posting
        var $composeStatus = $("#compose-status");
        var $postStatus = $("#post-status");

        $('.update .delete').click(removeStatusPost);

        $postStatus.click(function () {
            var statusBody = $composeStatus.val();
            if (statusBody.length == 0) return;

            $.ajax({
                type: "POST",
                url: "/post-status/",
                data: {
                    csrfmiddlewaretoken: csrfTOKEN,
                    status_update: statusBody,
                    profile_id: pk,
                },
                success: function (update) {
                    $composeStatus.val("");
                    $("#updates-stream-content").prepend(update);
                    $("#updates-stream-content .delete").click(removeStatusPost);
                },
            });
        });

        var $secondaryContent = $("#secondary-content"),
            $mainContent = $("#main-profile-content"),
            $fansList = $("#fans-list"),
            $showsList = $("#events"),
            updatesHeight = $secondaryContent.outerHeight(),
            fansHeight = $fansList.outerHeight();

        //secondary-content trigger
        $secondaryContent.find(".trigger").on("click", function () {
            //highlight item
            $secondaryContent.find(".trigger").removeAttr("selected");
            $(this)[0].setAttribute("selected", "true");

            //show area
            var target = $(this).attr("opens");
            $secondaryContent.find("> div").hide();
            $(target).show();
        });

        function removeStatusPost(){
            var $post = $(this);
            var post_id = $post.attr('record-id');
            $.ajax({
                type: "POST",
                url: "/delete-post-ajax/",
                data: {
                    csrfmiddlewaretoken: csrfTOKEN,
                    post_id: post_id,
                },
                success: function (update) {
                    $post.remove();
                },
            });
        }

        function post_layout_setting(which, val) {
            $.ajax({
                type: "POST",
                url: "/profile-layout-setting",
                data: {
                    csrfmiddlewaretoken: csrfTOKEN,
                    which: which,
                    val: val,
                },
            });
        }

        function refreshUpdatesHeight(speed) {
            // I/P: speed (number) (optional)
            // O/P: no return value
            //
            // Updates second column layout based on updatesHeight

            if (speed == undefined) speed = 0;
            mainContentHeight = updatesHeight == 32 ? 934 : 934 - updatesHeight;
            $secondaryContent.animate(
                {
                    height: updatesHeight + "px",
                },
                speed
            );
            $secondaryContent.find("#scrollbar-screen-updates").animate(
                {
                    height: updatesHeight - 83 + "px",
                },
                speed
            );
            $secondaryContent.find("#reviews").animate(
                {
                    height: updatesHeight - 34 + "px",
                },
                speed
            );
            $mainContent.animate(
                {
                    height: mainContentHeight + "px",
                },
                speed
            );
            $mainContent.find("#scrollbar-screen-releases").animate(
                {
                    height: mainContentHeight - 34 + "px",
                },
                speed
            );
            $mainContent.find("#scrollbar-screen-fand-content").animate(
                {
                    height: mainContentHeight - 66 + "px",
                },
                speed
            );
        }

        function refreshFansHeight(speed) {
            // I/P: speed (number) (optional)
            // O/P: no return value
            //
            // Updates third column layout based on fansHeight

            if (speed == undefined) speed = 0;
            eventsHeight = fansHeight == 32 ? 934 : 934 - fansHeight;
            $fansList.animate(
                {
                    height: fansHeight + "px",
                },
                speed
            );
            $fansList.find("#scrollbar-screen-fans").animate(
                {
                    height: fansHeight - 34 + "px",
                },
                speed
            );
            $showsList.animate(
                {
                    height: eventsHeight + "px",
                },
                speed
            );
            $showsList.find("#scrollbar-screen-events").animate(
                {
                    height: eventsHeight - 34 + "px",
                },
                speed
            );
        }

        function refreshUpdatesVisibility($elem, height) {
            if (height == 32) {
                $elem.animate({ opacity: 0.4 }, 200).addClass("hidden");
            } else {
                $elem.animate({ opacity: 1.0 }, 200).removeClass("hidden");
            }
        }

        $(".drag-handle").each(function () {
            $(this).draggable({
                boundaryParent: null,
                dontAnimate: true,
                autoPosition: false,
                x: false,
                callbacks: {
                    move: function (e, a, $this) {
                        var y = a.y,
                            $container = $this.parent().parent();

                        switch ($container[0].id) {
                            case "secondary-content":
                                // Don't let them go below 32
                                updatesHeight = Math.min(
                                    934,
                                    Math.max(32, updatesHeight - y)
                                );
                                refreshUpdatesHeight();
                                break;
                            case "fans-list":
                                fansHeight = Math.min(
                                    934,
                                    Math.max(32, fansHeight - y)
                                );
                                refreshFansHeight();
                        }
                    },
                    mouseup: function (e, $this) {
                        switch ($this.parent().parent()[0].id) {
                            case "secondary-content":
                                if (updatesHeight > 850) {
                                    updatesHeight = 934;
                                    refreshUpdatesHeight(200);
                                } else if (updatesHeight < 120) {
                                    updatesHeight = 32;
                                    refreshUpdatesHeight(200);
                                }
                                refreshUpdatesVisibility(
                                    $secondaryContent,
                                    updatesHeight
                                );
                                post_layout_setting(
                                    "updatesHeight",
                                    updatesHeight
                                );
                                break;

                            case "fans-list":
                                if (fansHeight > 850) {
                                    fansHeight = 934;
                                    refreshFansHeight(200);
                                } else if (fansHeight < 120) {
                                    fansHeight = 32;
                                    refreshFansHeight(200);
                                }
                                refreshUpdatesVisibility($fansList, fansHeight);
                                post_layout_setting("fansHeight", fansHeight);
                                break;
                        }
                    },
                },
            });
        });

        $("#main-picture img").click(function () {
            var $visuals = $("#dropdown-visuals"),
                $visualElements = $visuals.find(".visual-elements"),
                $pictureAndButtons = $("#picture-and-buttons"),
                elementHeight = 160,
                desired =
                    Math.ceil($visuals.find(".visual-element").length / 6) *
                    elementHeight;

            $visualElements.css("height", desired + "px");

            if ($visuals.height() == 0) {
                $visuals.css("height", desired + "px");
                if (desired > elementHeight * 2) {
                    // $pictureAndButtons.addClass('is-open');
                }
            } else {
                // $visuals.css("height", 0);
                // $pictureAndButtons.removeClass('is-open');
            }
        });

        function openLightboxForVisual($self) {
            hearo.lightbox.queue = [];
            $(".visual-element").each(function () {
                hearo.lightbox.queue.push(this);
            });

            if ($self.attr("picture")) {
                var i = new Image();
                i.onload = function () {
                    var $container = $("<div></div>");
                    $container.append(this);
                    $container.append(
                        $(
                            '<div class="caption">' +
                                $self.attr("caption") +
                                "</div>"
                        )
                    );
                    hearo.lightbox.show($container, this.width, this.height);
                };
                i.src = $self.attr("picture");
            } else if ($self.attr("video")) {
                hearo.lightbox.show(
                    $(
                        '<iframe width="640" height="480" src="//www.youtube.com/embed/' +
                            $self.attr("video") +
                            '" frameborder="0" allowfullscreen></iframe>'
                    )
                );
            }
            hearo.lightbox.current = $self[0];
            hearo.lightbox.openMethod = openLightboxForVisual;
        }

        $(".visual-element").click(function () {
            openLightboxForVisual($(this));
        });

        $(function () {
            if (!$("#modal-container").length) {
                $("html, body").scrollTop($("#top-gallery").height());
            }
        });
    };

    var inAjaxCall = false;
    var page = 1;
    var scrollEnabled = true;

    function getUpdates() {
        if (inAjaxCall || !scrollEnabled) {
            return;
        }

        var keyword = $("#updates-stream-content").attr("data-keyword");

        inAjaxCall = true;
        page = page + 1;
        $.ajax({
            dataType: "json",
            url: "/feeds/",
            data: {
                page: page,
                keyword: keyword,
            },
            success: function (data) {
                inAjaxCall = false;
                $(".loader").hide();
                $("#updates-stream-content").append(data.html);
                scrollEnabled = data.more;
            },
            error: function (data) {
                inAjaxCall = false;
                $(".loader").hide();
            },
        });
    }

    window.initUpdate = function () {
        $("#updates-stream-content").endlessScroll({
            fireOnce: false,
            fireDelay: false,
            loader: "",
            callback: function () {
                if (!scrollEnabled) {
                    return;
                }
                $(".loader").show();
                getUpdates();
            },
        });
    };

    /*
     * global exports
     */

    //  hearo.setup.node = setup;

    hearo.setup.profile = setup;
})();
