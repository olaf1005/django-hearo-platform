/*global
$,
createElem,
console,
csrfTOKEN,
userTab,
getChecked,
sliderState,
makeAdmin,
splitOnComma,
extractLast,
setupListeners,
warningText,
showAreYouSure,
DOWNLOAD_FORMATS,
deleteAlbum,
showAlbumDialog,
addAlbumEvents,
moveToCurrent,
moveToPool,
inviteHtml,
autocompleteAll,
getSortedGenres,
getSortedInstruments,
createBannerUploadLightbox,
commitLegalPage,
editLegalPage,
alert */



(function () {
    var flashSuccess = function (msg) {
    }

    var flashError = function (msg) {
        if (msg) {
            var s = $("#dashboard_error").show();
            s.text(msg);
            setTimeout(function () { s.fadeOut(1000); }, 500);
        } else {

        }

    };

    /* Profile */

    function musicianShow() {
        $('[musicianonly]').show();
    }

    function musicianHide() {
        $('[musicianonly]').hide();
    }

    function getFont(radios) {
        var czechd, i;
        czechd = "'Permanent Marker', cursive";
        for (i = 0; i < 3; i = i + 1) {
            if (radios[i].checked) {
                czechd = radios[i].value;
            }
        }
        return czechd;
    }

    function postBannerInfo() {
        var formData = new FormData();
        formData.append('csrfmiddlewaretoken', $('csrfTOKEN').text());
        formData.append('font', getFont($('.font')));
        formData.append('display_title', getChecked($('#id_name_bool')));
        formData.append('display_genre', getChecked($('#id_genre_bool')));
        formData.append('display_instrument', getChecked($('#id_instrument_bool')));
        formData.append('display_location', getChecked($('#id_location_bool')));
        formData.append('display_bar', getChecked($('#id_bar_bool')));
        formData.append('uploading_bool', getChecked($('#upload_chosen')));

        $.ajax({
            type: 'POST',
            url: '/my-account/banner-ajax/',
            data: formData,
            cache: false,
            contentType: false,
            processData: false
        });
        flashSuccess();
    }

    function uploadBannerImage() {
        console.info('uploadbannertemp');
        var formData = new FormData();
        formData.append('csrfmiddlewaretoken', window.csrfTOKEN);
        formData.append('texture', $('#id_banner_pic')[0].files[0]);
        $.ajax({
            type: 'POST',
            url: '/upload-banner-temp/',
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            complete: function (data) {
                createBannerUploadLightbox();
            }
        });
    }

    /* ----------------- Profile Info ------------------*/


    function setupProfileInfo() {
        autocompleteAll({
            '#id_instruments': 'instruments',
            '#id_genres': 'genres'
        });
    }
    /* -----------------LOCATION ---------------------*/

    /*
        changes the users public location and notifies them of any
        collision found by the geocoder
            calls my_account_location_ajax() in accounts.views.py
    */
    function changeLocation() {
        $(".errorMessage").hide();
        $("#successMessage").hide();

        $('#id_city').loader();

        $.ajax({
            type: 'POST',
            url: '/my-account/location-ajax/',
            dataType: 'json',
            data: {
                'csrfmiddlewaretoken': csrfTOKEN,
                'value': $("#id_city").val()
            },
            success: function (data) {
                $('#id_city').suggest(data, {
                    callback: function () {
                        $("#check").text('Checked').css('background', 'rgba(0,100,0,.8)');
                    }
                });

            },
            complete: function () {
                $('#id_city').stoploader();
            }
        });
    }
    /**
        called when the user resolves a location collision by clicking the
        location that suits him/her best
            loc is a string representing a specific city geopy can accept
            my_account_clarify_location_ajax which sets the location field of a user
            as the geopy specific location (loc)

            on success: show a message!
    */
    function clarifyLocation(loc) {
        $.ajax({
            type: 'POST',
            url: '/my-account/clarify-location-ajax/',
            data: {
                'csrfmiddlewaretoken': csrfTOKEN,
                'city': loc
            },
            success: function (data) {
                $("#choices").children().remove();
                $('#id_city').val(data);
                $('#check').text('Checked');
                $('#check').css('background', 'rgba(0,100,0,0.8)');
            }
        });
    }

    function register() {
        var email = $("#id_email").val();
        if (email == 'email') {
            email = ''
        }
        window.location.href = '/join/?email=' + encodeURIComponent(email);
    }
    /**
        called when user clicks login button.  Will either successfully log
        user in or display that user has incorrect password or email.
    */
    function logIn() {
        var email = $("#id_email").val();
        var data = {
            csrfmiddlewaretoken: csrfTOKEN,
            email: email,
            password: $("#id_password").val(),
            next: $("#next").val()
        };
        if ($("#next").val() && $("#next").val() != 'None') {
            data['next'] = $("#next").val();
        }
        $('#submit-login').addClass('disabled');
        $.ajax({
            type: 'POST',
            url: '/login/',
            data: data,
            success: function (data) {
                $('#submit-login').removeClass('disabled');
                if (data === "wrong_email") {
                    $('#loginErrorMessage').text("The email address you have entered does not match an existing user account.");
                    $('#loginErrorMessage').show();
                    $('#loginErrorMessage').fadeIn().delay(3000).fadeOut('slow');
                }
                else if (data === "wrong_password") {
                    $('#loginErrorMessage').text("Incorrect password. ")
                        .append(createElem('a', { 'id': 'recovery_link', 'href': '/password-recovery/?email=' + encodeURIComponent(email) }, 'Forgot your password?'));
                    $('#loginErrorMessage').show();
                    $('#loginErrorMessage').fadeIn().delay(5000).fadeOut('slow');
                }
                else if (data === "not_verified") {
                    $('#loginErrorMessage').text("You need to follow the verification link we send you via email to login. ")
                        .append(createElem('a', { 'id': 'verification_link', 'href': '/not-verified/?email=' + encodeURIComponent(email) }, 'Resend verification email.'));
                    $('#loginErrorMessage').show();
                    $('#loginErrorMessage').fadeIn().delay(5000).fadeOut('slow');
                }
                else if (data.content) {//this will be a render_appropriately call
                    $("#content").html(data.content);
                    setupListeners();
                } else {
                    ajaxGo(data);
                    $.get("/refresh-header/", function (html) {
                        $("#header-bar").html(html);
                        setupListeners();
                    });
                    hearo.player.initialize();
                }
            }
        });
    }

    function sendVerification() {
        $.ajax({
            url: '/send-verification/',
            type: 'POST',
            data: { csrfmiddlewaretoken: csrfTOKEN, 'email': $("#verification_email").text() },
            success: function (response) {
                $("#verification_sent").fadeIn().delay(2000).fadeOut(2000);
            }
        });
    }
    /*
    called when the user submits their email to be emailed a recovery password
    */
    function sendRecovery() {
        $.ajax({
            url: "/send-recovery/",
            type: "POST",
            data: { csrfmiddlewaretoken: csrfTOKEN, 'email': $("#recovery_email").val() },
            success: function (response) {
                if (response === 't') {
                    $("#recovery_sent").fadeIn().delay(2000).fadeOut(2000);
                } else {
                    $("#recovery_failed").fadeIn().delay(2000).fadeOut(2000);
                }
            }
        });
    }

    /**
        Called when user saves new legal address in the dashboard.  If artist agreement
        is not checked, will flash error message accordingly.  If it is, it will
        attempt to save the address, and if succesful (i.e. address was validated),
        will flashSuccess
    */
    function changePrivateLocation() {
        $.ajax({
            type: 'POST',
            url: '/my-account/private-location-ajax/',
            data: {
                'csrfmiddlewaretoken': csrfTOKEN,
                'address1': $("#id_paddress1").val(),
                'address2': $("#id_paddress2").val(),
                'state': $("#id_pstate").val(),
                'zip': $("#id_pzip").val(),
                'city': $("#id_pcity").val()
            },

            success: function (data) {
                commitLegalPage();
                if (data === "succeeded") {
                    flashSuccess();
                } else {
                    flashError(data);
                }
            }
        });
    }

    /* ----------------VIDEO -------------------------*/
    /*
        ajax call to add a video to a profile's account
        called from the video-tab template in my-account
        reads a given youtube url, parses it for the v=
        and calls the upload_video_ajax view in accounts.views.py
        TODO: success() call and template better (styling)
    */
    function addVideo() {
        var urlTag, text, video_id, ampersandPosition, video_tr, td1, td2;
        urlTag = $("#youtube_url");
        text = urlTag.val();
        video_id = text.split('v=')[1];
        if (video_id) {
            ampersandPosition = video_id.indexOf('&');
            if (ampersandPosition !== -1) {
                video_id = video_id.substring(0, ampersandPosition);
            }
            $.ajax({
                type: 'POST',
                url: '/my-account/videos/upload-video-ajax',
                data: {
                    'csrfmiddlewaretoken': csrfTOKEN,
                    'video_id': video_id
                },

                success: function (data) {
                    $('#videos').prepend(data);
                    $("#videos .empty_media").hide();
                    urlTag.val("");
                },
                error: function (data) {
                    $(".errorMessage").text(data);
                    $(".errorMessage").show();
                    $(".errorMessage").fadeIn().delay(3000).fadeOut('slow');
                }
            });
        }
        else {
            $(".errorMessage").text("badly formatted youtube video url!");
            $(".errorMessage").show();
            $(".errorMessage").fadeIn().delay(1000).fadeOut('slow');
        }
    }
    /* ajax call to delete a video from a users profile
        called from the video tab template file when a user
        presses the delete button next to the video
    */
    function deleteVideo(video_id) {
        var tag = $("#video_" + video_id);
        $.ajax({
            type: 'GET',
            url: '/my-account/videos/delete-video-ajax',
            data: {
                'video_id': video_id
            },
            success: function (data) {
                tag.remove();
                if ($('.video_row').length === 0) { $("#videos .empty_media").show(); }
            }
        });
    }

    /* albums */
    function indexSongs() {
        $("#current_album_songs #current_song_scrollbox").children().each(function (i, div) {
            var html, song = $(div).find('.song_tab');

            song.html((i + 1) + '. ' + song.attr('name'));
        });
    }

    function populateAlbumSongs(albumid) {
        $.get('/get-album-songs', { 'albumid': albumid }, function (data) {
            var parsed = $.parseJSON(data);
            $.each(parsed, function (i, song) {
                var div, id = song.id + "_song";
                div = $("#" + id).parent();
                moveToCurrent(div, 't');
            });
        });
    }
    function moveToCurrent(div, append) {
        div.find('.delete_button').css('display', 'inline-block')
            .unbind('click')
            .click(function () {
                moveToPool(div);
            });
        if (append) { $("#current_album_songs #current_song_scrollbox").append(div); }
        else { $("#current_album_songs #current_song_scrollbox").prepend(div); }
        div.unbind('mouseover').unbind('mouseout');
        div.find('.make_current').hide();
        indexSongs();
    }
    function moveToPool(div) {
        div.find('.delete_button').hide().unbind('click');
        var mc, song_tab = div.find('.song_tab');
        song_tab.html(song_tab.attr('name'));
        $("#songs .scrollbox").prepend(div);
        mc = div.find('.make_current');
        div
            .mouseover(function () { mc.show(); })
            .mouseout(function () { mc.hide(); });
        mc.click(function () {
            moveToCurrent(div);
        });
        setTimeout(function () {
            mc.click(function () { moveToCurrent(div); });
        }, 200);
        indexSongs();

    }
    function saveAlbumSongs(id) {
        var ids = [];
        $("#current_album_songs #current_song_scrollbox").children().each(function (i, div) {
            ids.push($(div).find('.song_tab')[0].id.split('_')[0]);
        });
        ids = ids.join(',');
        $.ajax({
            type: "POST",
            url: "/save-album-songs/",
            data: {
                'albumid': id,
                'csrfmiddlewaretoken': csrfTOKEN,
                'songs': ids
            },
            success: function (data) {
                // todo: this doesn't seem to do anything, no element save_success exists
                // var s = $("#save_success");
                // s.show();
                // setTimeout(function(){s.fadeOut(1000);},500);
            },
            error: function (data) {
                // todo: this doesn't seem to do anything, no element save_error exists
                // var s = $("#save_error");
                // s.show();
                // setTimeout(function(){s.fadeOut(1000);},500);
            }
        });
    }
    //takes JSON from the showAlbumDialog function
    function addAlbum(data, edit) {
        var div, album = $.parseJSON(data)[0];
        if (edit) {
            div = $("#" + album.id + "_album");
            div.empty();
            $("#current_album").find('#' + album.id + "_cover").remove();
        }
        else {
            div = $(createElem('div', { className: 'album_row', 'id': album.id + "_album" }));
            $("#albums .scrollbox").append(div);
        }
        div
            .append(createElem('div', { className: 'delete_button' }))
            .append($(createElem('div', { className: 'img' }))
                .append(createElem('img', { 'src': album.small_cover })))
            .append($(createElem('div', { className: 'title' }))
                .append(createElem('div', { className: 'ellipsis' }, album.title))
                .append(createElem('span', {}, album.year_released))
                .append(createElem('span', {}, album.pretty_price)))
            .append($(createElem('input', { className: 'big-green edit_button', 'value': 'edit', 'type': 'button' }))
                .css('display', 'none'));
        $("#current_album").append($(createElem('img', { 'src': album.medium_cover, 'id': album.id + "_cover" })));
        addAlbumEvents(div);
        div.click();
    }
    function setupAlbums() {
        $(".album_row").each(function (i, row) {
            addAlbumEvents(row);
        });
        $("#current_album_songs #current_song_scrollbox").sortable({
            revert: true,
            stop: indexSongs,
            cancel: '.delete_button'
        });

        $("#add_album").click(function () {
            showAlbumDialog(
                function (data) { addAlbum(data, false); },
                function () {
                    flashError('Album saved unsuccessfully');
                }
            );
        });
    }

    function addAlbumEvents(album_row) {
        var id, name = $(album_row).find('.title').find('span').html();
        id = $(album_row)[0].id.split('_')[0];
        $(album_row)
            .mouseover(function () {
                $(this).find('.title').css('background', 'rgba(0,0,0,.1)');
                $(this).find('.delete_button').show();
                $(this).find('.edit_button').show();
            })
            .mouseout(function () {
                $(this).find('.title').css('background', 'rgba(0,0,0,.03)');
                $(this).find('.delete_button').hide();
                $(this).find('.edit_button').hide();
            })
            .click(function () {
                // todo: element does not exist, remove/replace
                // $("#album_songs_save").show().unbind('click').click(function(){
                //    saveAlbumSongs(id);
                // });
                $("#current_album").children().hide();
                $("#current_album_songs .empty_media").hide();
                $("#current_album_songs #current_song_scrollbox").children().each(function (i, song) {
                    moveToPool($(song));
                });
                $("#current_album #" + id + "_cover").show();
                populateAlbumSongs(id);

                $("#songs .scrollbox").children()
                    .mouseover(function () { $(this).find('.make_current').show(); })
                    .mouseout(function () { $(this).find('.make_current').hide(); });
                $("#songs .scrollbox").children().each(function (i, child) {
                    $(child).find('.make_current').click(function () {
                        moveToCurrent($(child));
                    });
                });
                $("#songs h4").html("Add Songs");
                //reset all the others
                $(".album_row").unbind('mouseover').unbind('mouseout')
                    .mouseover(function () {
                        $(this).find('.title').css('background', 'rgba(0,0,0,.1)');
                        $(this).find('.delete_button').show();
                        $(this).find('.edit_button').show();
                    })
                    .mouseout(function () {
                        $(this).find('.title').css('background', 'rgba(0,0,0,.03)');
                        $(this).find('.delete_button').hide();
                        $(this).find('.edit_button').hide();
                    })
                    .find('.title').css('background', 'rgba(0,0,0,.03)');
                //set the clicked one to be darker
                $(this).unbind('mouseover').unbind('mouseout')
                    .mouseover(function () {
                        $(this).find('.delete_button').show();
                        $(this).find('.edit_button').show();
                    })
                    .mouseout(function () {
                        $(this).find('.delete_button').hide();
                        $(this).find('.edit_button').hide();
                    })
                    .find('.title').css('background', 'rgba(0,0,0,.15)');

            })
            .find('.delete_button').unbind('click').click(function (e) {
                e.stopPropagation();
                var id = $(album_row)[0].id.split("_")[0];
                showAreYouSure(
                    warningText('Are you sure you want to delete ' + name + '?'),
                    function () { deleteAlbum(id); });
            });

        $(album_row).find('.edit_button').unbind('click').click(function (e) {
            e.stopPropagation();
            $.get('/get-album', { 'albumid': id }, function (data) {
                var album = $.parseJSON(data)[0];
                showAlbumDialog(
                    function (data) {
                        addAlbum(data, true);
                    },
                    function () {
                        flashError('Edited unsuccessfully');
                        $('.errorMessage').css({ 'left': '71px', 'top': '-53px', 'height': '22px', 'padding-top': '0px' });

                    },
                    album);
            });
        });

    }
    function deleteAlbum(id) {
        $.ajax({
            type: 'POST',
            url: '/delete-album-ajax/',
            data: {
                'csrfmiddlewaretoken': csrfTOKEN,
                'albumid': id
            },
            success: function (data) {
                $("#" + id + "_album").remove();
                $("#current_album").children().hide();
                $("#current_album .empty_media").show();
                $("#current_album_songs #current_song_scrollbox").empty();
                $("current_album_songs .empty_media").show();
                $("#" + id + "_cover").remove();
            }
        });
    }
    /* -----------------USER SETTINGS ---------------*/


    /* ------------------- SONG DETAILS ------------------- */

    // Make the row representing song details editable
    function typeFieldChange() {
        $(".myAccount_songRow select option:selected").each(function () {
            if ($(this).val() === 'normal' || $(this).val() === 'name_price') {
                $("#edit_price").show();
                $("#no_price").hide();
            } else {
                $("#edit_price").hide();
                $("#no_price").show();
            }
        });
    }

    // Parse the price field as a float to normalize output, mark as invalid if can't be parsed
    function priceFieldBlur() {
        var val;
        val = parseFloat($(this).val());
        if (isNaN(val)) {
            $(this).addClass("invalid-price");
        } else {
            $(this).removeClass("invalid-price");
            $(this).val(val.toFixed(2));
        }
    }

    function cancelEdits() {
        $("#edit_title, #edit_type, #edit_price, #no_price, #save_changes, #cancel_changes").remove();
        $(".info-title, .info-type, .info-price, .info-edit").show();
        $("#uploadedSongs").attr('editing', 'false');
    }

    function saveEdits(row) {
        var data;
        data = {
            'id': $(row.children(".info-id")).text(),
            'title': $("#edit_title").val(),
            'download_type': $("#edit_type").val(),
            'price': $("#edit_price").val(),
            'csrfmiddlewaretoken': $("#csrf_token").text()
        };
        $.ajax('/my-account/song-details/', {
            'type': 'POST', 'data': data, 'success': function (data, status) {
                var message, parsed;

                message = $("#editing_errors");
                parsed = $.parseJSON(data);
                if (status !== 'success') {
                    message.text('An error occurred.');
                    message.addClass('errorMessage');
                }
                else if (parsed && parsed.error) {
                    message.text(parsed.error);
                    message.addClass('errorMessage');
                } else {
                    message.removeClass('errorMessage');
                    $(row.find(".info-title")).text($("#edit_title").val());
                    $(row.find(".info-type")).text($("#edit_type :selected").text());
                    if ($("#no_price").is(":visible")) {
                        $(row.find(".info-price")).text("-");
                    } else {
                        $(row.find(".info-price")).text($("#edit_price").val());
                    }
                }
                cancelEdits();
            },
            'error': function () {
                var message;
                message = $("#editing_errors");
                message.text('An error occurred.');
                message.addClass('errorMessage');
                cancelEdits();
            }
        });
    }

    function editSong(row) {
        var table, titleSpan, titleField, typeSpan, typeField, currType, priceSpan, price, noPrice, priceField, saveButton, cancelButton, options;

        table = $("#uploadedSongs");
        if (table.attr('editing') !== "false") {
            return false;
        }
        table.attr('editing', 'true');

        titleSpan = row.find(".info-title")[0];
        typeSpan = row.find(".info-type")[0];
        priceSpan = row.find(".info-price")[0];
        titleField = createElem('input', { 'type': 'text', id: 'edit_title', value: $(titleSpan).text() });
        typeField = createElem('select', { id: 'edit_type' });

        /* TODO: get this from the server and store it in the table? */
        options = {
            'none': 'Stream Only',
            'free': 'Free Download',
            'normal': 'Fixed Price',
            'name_price': 'Name Your Price'
        };

        $.each(options, function (k, v) {
            var option;
            option = createElem("option", { value: k }, v);
            typeField.add(option);
        });

        price = parseFloat($(priceSpan).text());
        if (!price) {
            price = 0.69;
        }
        priceField = createElem('input', { 'type': 'text', id: 'edit_price', value: price.toFixed(2) });
        noPrice = createElem('span', { id: 'no_price' }, '-');

        saveButton = createElem('span', { id: 'save_changes', className: 'clickable' }, 'Save');
        cancelButton = createElem('span', { id: 'cancel_changes', className: 'clickable' }, 'Cancel');

        $(titleSpan).parent().append(titleField);
        $(typeSpan).parent().append(typeField);
        $(priceSpan).parent().append(priceField, noPrice);
        $(row.find(".info-edit")[0]).parent().append(saveButton, cancelButton);

        $(titleSpan).hide();
        $(typeSpan).hide();
        $(priceSpan).hide();
        $(table.find(".info-edit")).hide();

        currType = $(typeSpan).text();

        $('#edit_type option:contains(' + currType + ')').prop('selected', true);

        $(typeField).change(typeFieldChange);
        $(typeField).trigger('change');
        $(priceField).blur(priceFieldBlur);
        $(saveButton).click(function () { saveEdits(row); });
        $(cancelButton).click(cancelEdits);

    }

    function bindEditClickEvents() {
        $("#uploadedSongs").attr('editing', 'false');
        $(".info-edit").click(function (e) {
            e.preventDefault();
            editSong($(this).parent().parent()); /* edit song take as input the row in the table */
        });
    }

    window.bindEditClickEvents = bindEditClickEvents;


    /* --------------- BANK INFO ----------------- */

    function updateBankInfo() {
        var name, acct_number, rout_number, err, success, data;

        flashSuccess = function (msg) {
            $('#cashout_status').text(msg).addClass('csuccess').removeClass('cerr')
        };

        flashError = function (msg) {
            $('#cashout_status').text(msg).addClass('cerr').removeClass('csuccess');
        };

        name = $("#bank_account_name").val();
        acct_number = $("#bank_account_number").val().replace(/\D/g, '');
        rout_number = $("#bank_routing_number").val().replace(/\D/g, '');

        if (!(name) || !(acct_number) || !(rout_number)) {
            flashError('Please fill in all fields.');
            return false;
        }

        if (isNaN(parseInt(acct_number, 10)) ||
            (acct_number.length < 4) ||
            (acct_number.length > 10)) {
            flashError('Please supply a valid bank account number.');
            return false;
        }

        if (isNaN(parseInt(rout_number, 10)) ||
            (rout_number.length < 9)) {
            flashError('Please supply a valid 9 digit routing number.');
            return false;
        }

        data = {};
        data.csrfmiddlewaretoken = csrfTOKEN;
        data.name = name;
        data.account_number = acct_number;
        data.routing_number = rout_number;

        $.ajax({
            type: "POST",
            url: "/payment/update_bank_info/",
            data: data,
            dataType: 'json',
            success: function (data) {
                if (data.error) {
                    flashError(data.error);
                    return false;
                } else {
                    flashSuccess('Bank information saved successfully.');
                    return true;
                }
            },
            error: function (e) {
                flashError("There was a problem contacting our servers. Please try again.");
                return false;
            }
        });

    }

    function cashOut() {
        $.ajax(
            {
                url: "/payment/cash_out/",
                type: "get",
                success: function (data) {
                    window.location.href = '/my-account/payment';
                }
            });
    }

    function removeCard(cardid) {
        $.ajax('/payment/remove_card', {
            type: 'POST',
            data: {
                delete: cardid
            },
            success: function (data) {
                $('#card_' + cardid).fadeOut(500);
            }
        });
    }

    function editLegalPage() {
        $('.committedInput').removeClass('committedInput');
        $('#legal-container input:text').show();
    }

    function commitLegalPage() {
        $('#legalEdit').show().one('click', editLegalPage);
        $('#legal-container input:text').each(function () {
            var $this = $(this);
            $this.addClass('committedInput').one('focus', function () {
                editLegalPage();
            });
        });
    }

    window.logIn = logIn;
    window.register = register;
    window.cashOut = cashOut;
    window.updateBankInfo = updateBankInfo;
    window.changePrivateLocation = changePrivateLocation;
    window.changeLocation = changeLocation;
    window.clarifyLocation = clarifyLocation;
    window.removeCard = removeCard;

    window.editLegalPage = editLegalPage;
    window.commitLegalPage = commitLegalPage;

    window.setupProfileInfo = setupProfileInfo;

    window.flashSuccess = flashSuccess;
    window.flashError = flashError;
    window.addVideo = addVideo;
    window.postBannerInfo = postBannerInfo;
    window.deleteVideo = deleteVideo;
    window.getFont = getFont;
    window.setupAlbums = setupAlbums;
    window.uploadBannerImage = uploadBannerImage;

    window.sendRecovery = sendRecovery;
    window.sendVerification = sendVerification;

}());
