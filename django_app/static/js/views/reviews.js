var reviews = {
    el: $("#secondary-content"),

    elemType: false,
    elemID: false,
    elemTitle: false,

    events: function () {
        var self = this;

        $(document).on("click", "#submit-review", function () {
            self._post();
        });
        $(document).on("mouseover", "button.reviews-star", function (e) {
            self._reviewStarHover(e);
        });
        $(document).on("mouseup", "button.reviews-star", function (e) {
            self._reviewStarUp(e);
        });
        $(document).on("mouseout", "button.reviews-star", function (e) {
            self._reviewStarOut(e);
        });
        $(document).on("keyup", "#reviews-compose-box textarea", function (e) {
            self._typing(e);
        });
    },

    initialize: function () {
        this.events();

        //if saved from setup
        if (this.elemType && this.elemID && this.elemTitle) {
            this.open(this.elemType, this.elemID, this.elemTitle);
        } else {
            //use default profile review
            $reviewButton = $("#profile-buttons .bttn--special-review");
            var elemType = $reviewButton.attr("elem-type");
            var elemID = $reviewButton.attr("elem-id");

            $("#reviews").attr("for", elemType + ":" + elemID);

            this._get();
        }
    },

    open: function () {
        $("#secondary-content > div").hide();
        $("#reviews").show();
        this.setup.apply(this, arguments);
    },

    setup: function (elemType, elemID, elemTitle) {
        //if reviews doesn' exist, save variables and exit
        if (!$("#reviews").length) {
            reviews.elemType = elemType;
            reviews.elemID = elemID;
            reviews.elemTitle = elemTitle;
            return true;
        }

        var self = this;
        artworkImg = new Image();
        $(".reviews-star").removeClass("hover").removeClass("set");

        //selected button
        // $("#secondary-content ul.blue.light li").removeAttr("selected");
        // $(
        //     "#secondary-content ul.blue.light li#reviews-trigger"
        // )[0].setAttribute("selected", "true");

        artworkImg.src = "/reviews/artwork/" + elemType + "/" + elemID;
        $("#reviews-focus-item-artwork").empty().append(artworkImg);

        $("#reviews").attr("for", elemType + ":" + elemID);
        $("#reviews-compose-box textarea")
            .val("")
            .attr("placeholder", "Review " + elemTitle + "...")
            .focus();

        $("html, body").animate(
            {
                scrollTop: $("#reviews-compose-box").offset().top,
            },
            500
        );

        this._get();
    },

    _get: function () {
        // Extract the model and the pk from the reviews bar's "for" attribute.
        if ($("#reviews").length == 0) {
            return;
        }

        $("#user-reviews").empty();

        var ident = $("#reviews").attr("for").split(":"),
            model = ident[0],
            pk = ident[1];

        $.getJSON("/get-reviews/", { model: model, id: pk }, function (data) {
            if (data['reviews_list'].length == 0) {
                // If there are no reviews
                $("#average-rating").hide();
                $("#user-reviews").append(
                    "<div empty id='no-reviews'>Be the first to review this " +
                        model +
                        "!</div>"
                );
            } else {
                // If there ARE reviews
                $("#average-rating").show();

                data['reviews_list'].map(function (review) {
                    $("#user-reviews").prepend(review.html);
                });

                setupLinks();
            }

            var mine = data['userinfo'];
            if (mine.user_reviewed) {
                $("#reviews-compose-box textarea").val(mine.review.review);
                $("#submit-review").text("Update").removeClass("disabled");
                for (var i = 1; i <= mine.review.stars; i++) {
                    $('.reviews-star[value="' + i + '"]').addClass("set");
                }
            } else {
                $("#submit-review").text("Submit").addClass("disabled");
            }

            var avg = data['avg_rating'];
            setAvgStars(avg);
        });
    },

    _post: function () {
        var ident = $("#reviews").attr("for").split(":"),
            model = ident[0],
            pk = ident[1],
            reviewContent = $("#reviews-compose-box textarea").val(),
            stars = $("button.reviews-star.set").length;

        $.ajax({
            url: "/post-review/",
            type: "POST",
            dataType: "json",
            data: {
                model: model,
                qid: pk,
                review: reviewContent,
                stars: stars,
                csrfmiddlewaretoken: csrfTOKEN,
            },
            success: function (data) {
                $(
                    '#user-reviews [reviewer="' + data.reviewer.id + '"]'
                ).remove();
                $("#user-reviews").prepend(data.html);
                $('#no-reviews').remove();
                setAvgStars(data.avg);
            },
        });
    },

    _reviewStarHover: function (e) {
        var $star = $(e.target),
            value = parseInt($star.attr("value"), 10);
        for (var i = 1; i <= value; i++) {
            $('button.reviews-star[value="' + i + '"]').addClass("hover");
        }
    },

    _reviewStarUp: function (e) {
        $("#reviews-stars .reviews-star").removeClass("set");
        $("#submit-review").removeClass("disabled");
        var $star = $(e.target),
            value = parseInt($star.attr("value"), 10);
        for (var i = 1; i <= value; i++) {
            $('#reviews-stars .reviews-star[value="' + i + '"]').addClass(
                "set"
            );
        }
    },

    _reviewStarOut: function (e) {
        $(".reviews-star").removeClass("hover");
    },

    _typing: function (e) {
        if ($(e.target).val().length > 5) {
            $("#submit-review").removeClass("disabled");
        } else if ($("#reviews-stars .reviews-star.set").length == 0) {
            $("#submit-review").addClass("disabled");
        }
    },
};

hearo.setup.reviews = reviews;
