/*global
  hearo,
  */

(function () {
    var setup = function () {
        /*
         * Helper methods
         */

        function validate_create_page() {
            if ($('#id_name').val() === '') {
                $('#id_name-container').addClass('input-error');
                return false;
            }
            return true;
        }

        function clear_create_page_validation_errors() {
            $('.input-error').removeClass('input-error');
        }

        function toggle_create_page_submit_spin() {
            $('#modal-create-page').toggleClass("disabled").toggleClass('spinning');
        }

        function create_page() {

            clear_create_page_validation_errors();

            if (!validate_create_page()) {
                return false;
            }

            toggle_create_page_submit_spin();

            setTimeout(function() {
                console.log('sleeping');
           }, 5000);

            var request;
            /* POST data from profile view to endpoint */
            if (request) {
                request.abort();
            }
            var request = $.ajax({
                type: "POST",
                dataType: "json",
                url: "/my-account/create-page-ajax/",
                data: {
                    csrfmiddlewaretoken: csrfTOKEN,
                    /* Account type */
                    name: $("#id_name").val(),
                    account_type: $("#acctype-sel li a.active").attr("id"),

                    /* Text */
                    biography: $('[name="biography"]:visible').val(),
                    influences: $('[name="influences"]:visible').val(),
                    experience: $('[name="experience"]:visible').val(),
                    goals: $('[name="goals"]:visible').val(),
                    genre: $('[name="genres"]:visible').val(),
                    instruments: $('[name="instruments"]:visible').val(),
                    city: $('[name="city"]:visible').val(),

                    /* Musician questions */
                    start_band: getChecked($("#id_start_band")),
                    join_band: getChecked($("#id_join_band")),
                    write_music: getChecked($("#id_write_music")),
                    teacher: getChecked($("#id_teacher")),
                    is_musician: getChecked($("#id_is_musician")),
                    producer: getChecked($("#id_producer")),
                    dj: getChecked($("#id_dj")),
                    engineer: getChecked($("#id_engineer")),
                    new_people: getChecked($("#id_new_people")),
                },
                success: function (data) {
                    setTimeout(update_inputs, 3000);
                    // pass
                    $("#modal-cancel").trigger('click');
                    document.location.href =
                        "/profile/" +
                        data["profile_keyword"] +
                        "?switchid=" +
                        data["profile_id"];
                },
                complete: toggle_create_page_submit_spin,
            });
        }

        function manage_members() {
            var groupid = $(this).attr("group-id");
            $.ajax({
                type: "POST",
                url: "/my-account/get-membership/",
                data: { csrfmiddlewaretoken: csrfTOKEN, id: groupid },
                dataType: "json",
                success: function (data) {
                    $("#edit_membership").html($(data["page_snippet"]));

                    $("button.make-admin").click(make_user_admin);
                    $("button.make-member").click(make_user_member);
                    $("button.delete").click(remove_user_from_page);

                    $("#user_v1-query").typeahead({
                        minLength: 1,
                        order: "asc",
                        dynamic: true,
                        hint: true,
                        delay: 500,
                        backdrop: {
                            "background-color": "#fff",
                        },
                        template:
                            '<span class="row">' +
                            '<span class="avatar">' +
                            '<img src="{' +
                            "{img_path}" +
                            '}">' +
                            "</span>" +
                            '<span class="username">{' +
                            "{name}" +
                            "} </span>" +
                            '<span class="location">{' +
                            "{location}" +
                            "}</span>" +
                            "</span>",

                        source: {
                            user: {
                                display: ["name", "keyword"],
                                href:
                                    "https://tune.fm/profile/{" +
                                    "{keyword}" +
                                    "}",
                                url: [
                                    {
                                        type: "GET",
                                        dataType: "json",
                                        url: "/search/get-invites/",
                                        data: {
                                            query: "{" + "{query}" + "}",
                                            groupid: groupid,
                                        },
                                        callback: {
                                            done: function (data) {
                                                for (
                                                    var i = 0;
                                                    i < data.data.people.length;
                                                    i++
                                                ) {
                                                    if (
                                                        data.data.people[i]
                                                            .location === null
                                                    ) {
                                                        data.data.people[
                                                            i
                                                        ].location = capitaliseFirstLetter(
                                                            data.data.people[i]
                                                                .account_type
                                                        );
                                                    }
                                                }
                                                return data;
                                            },
                                        },
                                    },
                                    "data.people",
                                ],
                            },
                        },
                        callback: {
                            onClick: function (node, a, item, event) {
                                console.info("Item clicked:", item);
                                sendRequestAjax(item.id, groupid);
                                return false;
                            },
                            onSendRequest: function (node, query) {
                                console.log(
                                    "request is sent, perhaps add a loading animation?"
                                );
                                return false;
                            },
                            onReceiveRequest: function (node, query) {
                                console.log(
                                    "request is received, stop the loading animation?"
                                );
                                return false;
                            },
                        },
                        debug: true,
                    });
                },
                error: function () {
                    alert("An error occurred fetching membership data.");
                },
            });
        }

        hearo.elements.savebutton.hide();

        /*
         * Bind event handlers
         */

        // buttons for pages
        $("#pending-pages ul li button.leave_page").on(
            "click",
            leave_pending_page
        );
        $("#pending-pages ul li button.join_group").on("click", join_group);

        $("#live-pages ul li button.leave_page").on("click", leave_live_page);
        $("#live-pages ul li button.manage_members").on(
            "click",
            manage_members
        );

        $("button.view_page").on("click", view_page);
        $("button.switch_to_profile").on("click", switch_profile);

        // buttons for membership administration
        $("button.make-admin").on("click", make_user_admin);
        $("button.make-member").on("click", make_user_member);
        $("button.delete").on("click", remove_user_from_page);

        $("#create-a-page").on("click", function () {
            setTimeout(setup_suggestions, 1000);
            setTimeout(update_inputs, 1000);
            $("id_name").trigger("click");
            // we set the modal-create-page on click even here
            $("#modal-create-page").on("click", create_page);
        });

        // onclick functionality is disabled until create-a-page is clicked
        $("#modal-create-page").on("click", function () {});

        /*
         * Other setup
         */

        modalEffectsInit();

        /*
         * $document.ready exports
         */
    };

    /*
     * global exports
     */

    window.hearo.setup.dashboard.pages = setup;
})();
