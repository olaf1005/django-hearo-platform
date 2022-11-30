/* etc.js
   helpers to export, so why bother with a module
 */


/* filter away methods and prototype chain from iterator
   for (x in l) {
    if (l.hasOwnProperty(x) && typeof(x) !== 'function') {

    }
   }
*/
function swap(array, i, j){
    var temp;
    temp = array[i];
    array[i] = array[j];
    array[j] = temp;
}
function splitOnComma( val ){
    return val.split(/,\s*/);
}
function extractLast( str ){
    return splitOnComma(str).pop();
}
function nextRequest() {
    requestId = requestId + 1;
    return requestId - 1;
}

function isVisible(el) {
    var top, left, width, height;
    top    = el.offsetTop;
    left   = el.offsetLeft;
    width  = el.offsetWidth;
    height = el.offsetHeight;

    while(el.offsetParent) {
      el   = el.offsetParent;
      top  = top  + el.offsetTop;
      left = left + el.offsetLeft;
    }

    return (
    top < (window.pageYOffset + window.innerHeight) &&
        left < (window.pageXOffset + window.innerWidth) &&
        (top + height) > window.pageYOffset &&
        (left + width) > window.pageXOffset
    );
}

function bind_anchor(a) {
    if( ! $(a).data("listening") && $(a).attr("href") && $(a).attr("href").indexOf("/logout") === -1 && !$(a).hasClass('ajax') && !$(a).hasClass('ui-slider-handle') )
    {
        $(a).data("listening", true);

        $(a).click( function(e) {
          unsearch(); //Search
          History.pushState({type: "link", httpReqType: "GET", data: null, requestid: nextRequest()},
                            null,
                            $(a).attr("href"));
                            e.preventDefault();
        });
    }
}

function uniqueid(){
    var string = '', x;
    for (x = 0; x < 11; x+=1){
      string += 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'.split('')[parseInt(Math.random() * 62, 10)];
    }
    return string;
}


//  createElem
//      Desc: makes any DOM element and gives it attributes and/or innerHTML, and can append other objects to it
//      Args:
//          a: string, name of element we're making
//          b: key:value map of attribute names and values. ex: { 'className': 'fan_button', 'id': 'fan_button_34' }
//          c: string, will be put into the element as innerHTML
//          d: list of already-defined elements to append to this element, in the order they're listed
//      Called by: any functions that generate HTML, usually using ajax data (ex: jam page, profile page)
//      Returns: the finished element

function createElem(a, b, c, d){ // artur's jawnpiece
    var x, i, e, h = a === 'a-external' ? true : false;

    if (h){
        a = 'a';
        b.target = '_newtab';
    }

    x = document.createElement(a);

    for (i in b){
        if (b.hasOwnProperty(i) && typeof(i) !== 'function') {
            x[i] = b[i];
        }
    }

    if (c !== undefined){
        x.innerHTML = c;
    }

    d = d || [ ];

    for (e in d){
        if (d.hasOwnProperty(e) && typeof(e) !== 'function') {
            x.appendChild(d[e]);
        }
    }

    if (a === 'a' && !h){
        bind_anchor(x);
    }

    if ($(x).hasClass('playSong')){ // Special case for song play buttons which usually get set when the doc loads.
        //bindPlaySong($(x));
    }
    else if ($(x).hasClass('playAlbum')){
        bindPlayAlbum($(x));
    }

    return x;
}

//  appendobj
//      Desc: runs appendChild on a load of objects listed in pairs inside of a main list [ [parent, child], [parent, child] ]
//      Args:
//          a: list containing smaller 2-item lists of parent, child pairs. This is iterated thru to append a bunch of children to parents
//      Called by: any functions that generate HTML, sometimes in conjunction with createElem
//      Returns: nothing
//      Note: I don't think this is actually in use, I forgot I put it in here. I'll start using it though because it's cleaner than a bunch of $(a).append(b)'s
//          -Artur

function appendobj(a){
    var i;

    for (i = 0; i < a.length; i=i+1){
    a[i][0].appendChild(a[i][1]);
    }
}

//  getChecked
//      Desc: returns 't' if checkbox object is checked, 'f' if unchecked
//      Args:
//          ob: checkbox object
//      Called by: ¯\_(ツ)_/¯ wherever a form is being validated. (I'm not sure why it's 't' and 'f' over true and false, I think Charlie wrote this? - Artur)
//      Returns: returns 't' or 'f' for true/false

function getChecked(object){
    return object.attr('checked') ? 't' : 'f';
}

function sliderState(ob){
    if(ob.find('.option_selected').html() === "yes"){
        return 't';
    }
    return 'f';
}

function sendFanMail(keyword, subject, body){
    if (keyword === undefined || subject === '' || body === ''){ return; }
    $.ajax({
        type: 'POST',
        url: '/mail/send-message/',
        data: {
            'csrfmiddlewaretoken': csrfTOKEN,
            'keyword' : keyword,
            'subject' : subject,
            'message' : body
        },
        success: function(html){
          fanmail.hide_mail_lightbox();
          //TODO: REBASE CHECK
          if($("#page_name").attr('value') === 'fanmail'){
            var $elt = $(html).hide();
            $elt.find('.message').click(messageClick);
            $("#sentbox").prepend($elt.fadeIn(500))
                .find('#mail_subhead').fadeOut(300);
	  }
          //END TODO
          setupLinks();
        }
    });
}

function formatTime( seconds ) {
    var mins, residualSeconds;
    mins = Math.floor( seconds / 60);
    residualSeconds = seconds - 60*mins;
    if( residualSeconds < 10 ) {
        residualSeconds = "0" + residualSeconds;
    }
    return mins + ":" + residualSeconds;
}

function formatPrice( price ) {
    var dollaBills, cents, str;
    if( price === null ) {
        return "NYP";
    }
    else if( price === 0 ) {
        return "FREE";
    }
    else {
        dollaBills = Math.floor(price / 100);
        cents = price % 100;
        str = dollaBills + ".";

        if( cents < 10 ) {
            str = str + "0" + cents;
    }
        else {
            str = str + cents;
    }

        return "$" + str;
    }
}

function shorten( string ) {
    if( string.length < 30 ) {
        return string;
    }
    else {
        return string.substring(0, 29) + "...";
    }
}

function processUrl( url ) {
    if( url.indexOf( "?") === -1 ) {
        return url + "?ajax=true";
    }
    else {
        return url + "&ajax=true";
    }
}

function dialog( title, message ) {
    alert( message );
}

function viewPhoto( filename ) {
    var cont,img,dialog,height,width;
    cont = $("#photoExpansion .photoContainer");
    cont.empty();
    cont.unbind( 'click' );
    img = document.createElement("img");
    $(img).attr('src', '/uploads/viewable/' + filename);
    dialog = cont.parent();
    $(img).load(function(e) {
        dialog.unbind( 'click' );
        img = e.target;
        height = img.height + 30;
        width = img.width + 40;
        cont.append( img );
        img = null;
        dialog.dialog({
            dialogClass: 'alert photoDialog',
            modal: true,
            height: height,
            width: width,
            resizable: false
        });
        dialog.click( function(e) {
            $(this).dialog('destroy');
        });
    });
}

function bind_anchor(a) {
    if( ! $(a).data("listening") && $(a).attr("href") && $(a).attr("href").indexOf("/logout") === -1 && !$(a).hasClass('ajax') && !$(a).hasClass('ui-slider-handle') )
    {
        $(a).data("listening", true);

        $(a).click( function(e) {
          unsearch(); //Search
          History.pushState({type: "link", httpReqType: "GET", data: null, requestid: nextRequest()},
                            null,
                            $(a).attr("href"));
                            e.preventDefault();
        });
    }
}

function clickclear(field, def, color){
    if (field.value === def) {
        var hex = (color === 'dark')?'#CCC':'#232323';
        $(field).val('').css({'color': hex});
    }
}

function clickrecall(field, def, color){
    if (field.value === '') {
        var hex = (color === 'dark')?'#1b1b1b':'#CCC';
        $(field).val(def).css({'color': hex});
    }
}

function attachMessageHover(msg, subj, id){
    $('#msg' + id).click(function(){
    $(this).html(msg).addClass('inboxMessageOpen').click(function(){
        $(this).removeClass('inboxMessageOpen').html(subj);
            $.get('/mail/mark-read/?id=' + id);
        attachMessageHover(msg, subj, id);
    });
    });
}

// DOM ELEMENTS TO BE USED EVERYWHERE contact artur with questions

// Hey girl, sit down and have yourself some tune.fm usertab.

// Pre: User's full name, photo URL, and profile URL
// Post: Returns a DOM div that's the standard way of displaying users all over the site.

function userTab(name, picture, url, keyword){
    var all, link, img;
    all = createElem('div', { className: 'usertab'});
    link = createElem('a', { className: 'name', href: url }, name);
    img = createElem('img', { src: picture, className:'picture'});
    $(link).prepend(img);
    $(all).append(link).attr('user', keyword);
    return all;
}

// TODO: remove this and replace with autocomplete
function userTabGraphic(name,picture, url, id){
    var all, link, img;
    all = createElem('div', { className: 'usertab' });
    link = createElem('span', { className: 'name'}, name);
    img = createElem('img', { src: picture, className: 'picture' });
    $(link).prepend(img);
    $(all).append(link);
    all.id = id;
    all.url = url;
    all.name = name;
    all.picture = picture;
    return all;
}
// Pre: Pass in model type and unique ID
// Post: generates a fan button for it, returns it
function small_fan_button(fand, target, id){
    var button;
    if (fand){
        button = createElem('div', { className: 'small_fand_button'+' fanbutton_' + target + '_' + id }, 'FAN\'D');
        $(button).click(function(event){
            unfan_this(target,id,function(){ set_small_button_fan(target,id); });
            event.stopPropagation();
        }).mouseover(function(){
            this.innerHTML = 'UNFAN';
        }).mouseout(function(){
            this.innerHTML = 'FAN\'D';
        })
        .attr('objtype', target)
        .attr('objid', id);
    } else {
        button = createElem('div', { className: 'small_fan_button'+' fanbutton_' + target + '_' + id }, 'FAN');
        $(button).click(function(event){
            fan_this(target, id, function(){ set_small_button_fand(target, id); });
            event.stopPropagation();
        }).attr(target+'_id', id)
          .attr('fan_button', target + id)
          .attr('objtype', target)
          .attr('objid', id);
    }

    return button
}


function generateSongListing(logged_in, s){
    //used in search
    return songListing(s.id,s.title,s.duration,s.price,
    s.reviews_count,{'name':s.artist.short_name,'img':s.artist.img_path,'url':s.artist.url, 'logged_in':logged_in},
    s.fanned, s.download_type)
}


function generateAlbumListing(logged_in, a){
    //used in search
    return albumListing(a.id,a.title,a.small_cover,a.pretty_price,
    {'name':a.artist.short_name,'img':a.artist.img_path,'url':a.artist.url + "/?albumid="+a.id, 'logged_in':logged_in},
    a.fanned)
}
// Pre: Song's id, name, length (pre-formatted plz), price, and userTab object, and if the current user has fanned this song or not
// Post:  o - sup
//       _|_
//        |
//       / \

function songListing(song_id, name, duration, price, reviews_count, usertab, fanned, download_type, logged_in){
    //this is used by search
    var all, title, title_span, song_usertab, song_title, play, play_button, play_button_div, play_duration,
        download, download_button, download_button_div,
        reviews, reviews_button, reviews_button_div,
        fan, fan_button;

    all = createElem('tr', { className: 'song_listing', id: 'song_' + song_id });
    $(all).attr('songid', song_id);

    song_usertab = createElem('td', { className: 'search_songs_artist' });
    song_title = createElem('td', { className: 'search_song_name'});

    title_span = createElem('div', { className: 'search_song_title' }, name);
    $(title_span).addClass('ellipsis');
    if (usertab){
        $(song_usertab).append(new userTab(usertab.name, usertab.img, usertab.url))
    }
    $(song_title).append(title_span);

    play = $(createElem('td')).css('width','10%');
    play_button = createElem('a', { className: 'ajax playSong', 'songid': song_id });
    play_button_div = createElem('div', { className: 'song_play_button', 'songid': song_id });


    $(play_button).attr('songid', song_id);
    $(play_button_div).attr('songid', song_id);
    $(play_button).css('position','relative');
    $(play_button).css('top','5px');


    play_duration = createElem('span', { className: 'song_listing_text' }, duration);
    $(play).append(play_button).append(play_duration);
    $(play_button).append(play_button_div);

    fan = createElem('td', { width: '50'});
    if(logged_in){
        fan_button =  small_fan_button(fanned, 'song', song_id); // Baw baw baw
    }
    else{
        fan_button = $(createElem('div',{className : "small_fan_button", 'id':'fanbutton'},'FAN'));
        e = $(createElem('div',{className : "tooltip_description"})).text('Log in or register to fan!').css({'display':'none'});
        fan_button.append(e);
    }
    $(fan).append(fan_button);

    $(all).append(play).append(song_usertab).append(song_title);
    $(all).append(fan);
    return all;
}


//songids is a string of space separated ids

function albumListing(album_id, name, cover_src, price, usertab, fanned, logged_in){
    //this is used by search
    var all, title, title_span, album_cover, album_cover_img,play,play_button, display_price, album_usertab_object,
        fan, fan_button, album_usertab;
    all = createElem('div', { className: 'search_albums_listing', id: 'album_' + album_id, 'height': '60' });

    title = createElem('div', { className: 'search_album_title' }, name);
    $(title).addClass('ellipsis');

    album_cover_link = createElem('a', { href: usertab.url });
    $(album_cover_link).addClass('search_album_cover');
    album_cover = createElem('img', { src: cover_src, className: 'search_albums_cover_image' });
    $(album_cover_link).append(album_cover);

    play = createElem('div', { width: '40', className:'search_albums_play'});
    play_button = createElem('a', { className: 'ajax playAlbum '+ album_id});
    play_button_div = createElem('div', { className: 'song_play_button', 'album_id': album_id });

    $(play).append(play_button);
    $(play_button).append(play_button_div);

    $(all).append(album_cover_link).append(play).append(title)

    if (price){
        download = createElem('td', { className: 'download_price_td'});
        download_button = createElem('a',  { className: 'ajax downloadSong' });
        download_button_div = createElem('div', { className: 'song_download_button' }, price);
        $(download).append(download_button);
        $(download_button).append(download_button_div);
    }
    // reviews = createElem('td', { width: '70'});
    // reviews_button = createElem('a',  { href: '' + name });
    // reviews_button_div = createElem('div', { className: 'song_reviews_button' }, 'review')
    // $(reviews).append(reviews_button);
    // $(reviews_button).append(reviews_button_div);
    fan = createElem('div', { width: '50', className: 'search_albums_fan'});
    if(logged_in){
        fan_button =  small_fan_button(fanned, 'album', album_id); // Baw baw baw
    }
    else{
        fan_button = $(createElem('div',{className : "small_fan_button", 'id':'fanbutton'},'FAN'));
        e = $(createElem('div',{className : "tooltip_description"})).text('Log in or register to fan!').css({'display':'none'});
        fan_button.append(e);
    }
    $(fan).append(fan_button);

    // if (price){
    //   $(all).append(download);
    //}
    //$(all).append(reviews).append(fan);
    $(all).append(fan);
    return all;
}

function albumTile(cover_src, album_id, usertab, title, fanned, song_data){
    var cover = createElem('img', { src: cover_src, className: 'fand_album_tile' }),
        cover_container = createElem('div', { className: 'fand_album_tile_container'}),
        display_title, info;

    display_title = title.length > 18 ? title.substring(0,20) + '...' : title; // Truncate it like it's hot

    info = createElem('div', { className: 'fand_album_tile_info'}, display_title + '<br>' + usertab.name);

    $(cover_container).click(function(){
        browseAlbum(cover_src,album_id, usertab, title, fanned, song_data);
    }).append(cover).append(info);
    return cover_container
}

function browseAlbum(cover_src,album_id,usertab, title, fanned, song_data){
    var table, header, home, s, goback, minicover, minicover_container, ut, fan_this_brotha;
    home = $('#fandAlbumsTable')
    header = $('#fandAlbumHeader')
    table = $('#fandAlbumTracks');

    home.hide();
    header.show().html('');
    table.show().html('');

    s = song_data;

    for (i = 0; i < s.length; i += 1){
        artist = s[i].artist;
        // False for usertab cos we aren't putting that in
        listing = new songListing(s[i].id, s[i].title, s[i].duration, s[i].price,
                                  s[i].reviews_count, false, s[i].fanned, s[i].download_type);
        $('#fandAlbumTracks').append(listing);
    }


    goback = createElem('a', { className: 'fandlib_goback' }, 'back to albums');
    $(goback).click(function(){
        back_to_album_tiles()
    });

    minicover = createElem('img', { src: cover_src, className: 'fandlib_mini_album_cover' }),
    minicover_container = createElem('div', { className: 'fandlib_mini_album_cover_container'});
    $(minicover_container).append(minicover);

    album_info = createElem('div', { className: 'fandlib_album_header_info'} );
    album_title = createElem('div', { className: 'fandlib_album_header_title'}, title);

    ut = new userTab(usertab.name, usertab.img, usertab.url);
    $(ut).css({'display': 'block', 'left': '0px'});

    fan_this_album = small_fan_button(fanned, 'album', album_id);
    $(fan_this_album).css('margin-left', '10px');
    $(album_info).append(album_title).append(ut);
    $(album_title).append(fan_this_album);

    header.append(goback).append(album_info).append(minicover_container);
}

function back_to_album_tiles(){
    $('#fandAlbumHeader').hide();
    $('#fandAlbumTracks').hide();
    $('#fandAlbumsTable').show();
}

function fanmail_button(profile){
    var l = $(createElem('a')).click(function(){
        fanmail.show_mail_lightbox({
            'name' : profile.name,
            'img_path' : profile.img_path,
            'url' : profile.url,
            'keyword' : profile.keyword,
        })
        .css({
            'display':'inline-block',
            'position':'relative',
            'right' : '0px',
            'top' : '0px'
        });
    });
    this.all = l.append(createElem('div', { className: 'fanmail_button_all' }));
}

function instrument_module(instrument){
    this.all = createElem('div', { className: 'instrument_module' }, instrument);
    this.icon = createElem('img', { src: '/public/images/instrument_module_icon.png', className: 'instrument_module_icon' });
    $(this.all).prepend(this.icon);
    return this.all;
}

function jam_listing_onair_indicator(){
    this.all = createElem('div', { className: 'jam_listing_onair_indicator' });
    return this.all;
}

function jam_listing_dtj_indicator(){
    this.all = createElem('div', { className: 'jam_listing_dtj_indicator' });
    return this.all;
}

function hearo_loader(){
    this.img = createElem('div', { className: 'hearo_loader' });
    return this.img;
}

/*
 * DEPRECATED
 * Use $.autosuggest
 * currently used by fanmail, autocomplete users to send to
 */
function makeAutocomplete(input, elem){
    elem.autocomplete({
        width:422,
        source: function( request, response  ) {
            //extract last term
            var values = $.ui.autocomplete.filter(input, extractLast(request.term));
            response(values.slice(0,15));

        },
        focus : function(){return false;},
        select: function(event, ui){
            var terms = splitOnComma(this.value);
            terms.pop();
            terms.push(ui.item.value);
            terms.push("");
            this.value = terms.join(", ");
            return false;
        }

    });
    $('.ui-autocomplete').css('background','rgba(255,255,255,.9)');
}


//choices for type: genres, instruments, locations,
function autocompleteAll(elt_type_pairs, clickcallback){
    var values = _.values(elt_type_pairs);
    $.ajax({
        type : 'GET',
        url  : '/get-autocomplete/',
        data : {'info' : JSON.stringify(values)},
        dataType : 'json',
        success:function(data){
            $.each(elt_type_pairs, function(elt,type){
                $(elt).localsuggest(data[type], { commas: true, callback: clickcallback });
            });
        }
    });
}


//  slider
//      Desc: This builds that slider thing at the top of the Jam page that lets you choose between People and Organizations
//      Args:
//          name:   the grey category name that shows up when no selection is made (cleared when selection made)
//          action: function fired when selection is made (right now this is refresh_directory)
//      Called by: setupJam()
//      Returns: nothing

    function slider(){
        this.selected = null;
        // The soundtrack for this JS object: http://soundcloud.com/christianity-whale/the-folgers-in-my-coffee-today
        return this;
    }

   slider.prototype.animate = function(pos, width, speed, func, parent){
        //if(pos < 15 && pos > 0){pos = 0;}
        $(parent).find('#earl').animate({
            'width': width + 'px',
            'left': pos + 'px'
        }, speed , 'easeOutExpo', func);

    }

    //func is the method to be called after the animation is complete
    slider.prototype.set = function(opt, func){
        var i, pos, width, speed, parsed, item, parent, $opt = $(opt);

        this.selected = $opt.html();


        // Calculating where the slider should go, how wide it should become, and how fast it should do do that.
        parent = $opt.parent();

        //btw this is magic
        pos = $opt.offset().left - parent.offset().left;
        width = $opt.outerWidth();

        speed = Math.abs($(parent).find('#earl').offset().left - parent.offset().left - pos);

        $(parent).find('.option_selected').each(function(){
            $(this).attr({'class': 'option'});
        });


        setTimeout(function(){
            $opt.attr({'class': 'option_selected'});
        }, speed * 1.5);

        this.animate(pos, width, speed,func, parent);
    }

function showProfileProgress(){
    $.get('/get-profile-progress-ajax/', function(data){
        var e,
            progress,
            todo,
            parsed = data;
        progress = parsed[0];
        todo = parsed[1];
        if (progress != 100){
            $('#progress_bar').show();
            todo.forEach(function(elt){
                e = $(createElem('div',{className:'option'},elt['name']));
                e.click(function(){
                    todo_slider.set(this,function(){
                        $("#todo_info").html(elt['description']);
                    });
                });
                $('#todo_slider').append(e);
            });
            w = $('.option').toArray().reduce(function(acc,elt){
                return acc + parseInt($(elt).css('width'),10) + parseInt($(elt).css('padding'),10)*2;
            },10);
            todo_slider = new slider();
            todo_slider.set($('.option')[0],function(){
                $("#todo_info").html(todo[0]['description']);
            });
            $('#todo_slider').css('width',w+'px');
        }
        //width = 75*num elements
    });
}
// Most of this can go I think
function resetAjaxLoader(){
    var loader= $("#ajax_darkness #loader");
   loader.css({
        'left': (($(window).width() - loader.width()) / 2) + 'px',
        'top': (($(window).height() - loader.height()) / 2) + 'px'
    });
    $('#ajax_darkness').css({
        'width': $(window).width() + 'px',
        'height': $(document).height() + 'px'
    });
}
function showAjaxLoader(){
    var darkness, gif;
    gif = $(createElem('div',{'id':'loader'}))
        .append(createElem('img',{'src':"/public/images/ajax-loader.gif"}));
    darkness = $(createElem('div',{'id':'ajax_darkness'})).append(gif);
    $("body").append(darkness);
    resetAjaxLoader();
    window.onresize=function(){
        resetAjaxLoader();
    }
}
function hideAjaxLoader(){
    $("#ajax_darkness").remove();
}

// TODO: remove this and replace with autocomplete
function makeUserDropdown(elt, list, clickFunc, url, data, duplicate_list){
    var url_call;
    if(url){url_call = url;}
    else{url_call = '/search/get-invites/'}
    $.ajax( url_call,
        { data: $.extend({ 'query': $(elt).val(),
              ajax:  true,
              page:  0,
              id:   'default' }, data),
          success:  function(data){
            var profiles = data[0];
            list.empty();
            if(profiles){
                var already = [];
                if(duplicate_list){
                    already = $(duplicate_list).children().children().toArray().map(function(ob){return $(ob).attr('id');});
                }

                $.each(profiles, function(i,profile){
                    if(already.indexOf(String(profile.id)) == -1){
                        var u = new userTabGraphic(profile.name,profile.img_path,profile.url, profile.id);
                        $(u).click(clickFunc);
                        list.append($(createElem('div',{className:'user_row'})).append(u));
                    }
                });
            }
          },
          type:     "GET",
          dataType: "json"
      });
}
// TODO: remove this and replace with autocomplete
function addUserDropdown(elt, list, clickFunc, url, data, dup_list){
    $("#user_search").keydown( function(e) {
        setTimeout( function(){
            makeUserDropdown(elt,list,clickFunc, url,data, dup_list)
        }, 200 );
    });
}
function inviteHtml(name,picture,url){
    var div, t, tab;
    div = $(createElem('div',{'id':'invite_warning'}));
    t = $(createElem('span',{className:'warning_text'},'Are you sure you want to invite '));
    tab = new userTab(name,picture, url);
    q = $(createElem('span',{className:'warning_text'},'?')).css({'margin-left':'-29px'});
    div.append(t).append(tab).append(q);
    return div;
}
function warningText(text){
    var t = $(createElem('div',{className:'warning_text'},text));
    return t;
}
function closeAreYouSure(){
    $('#ajax_darkness').remove();
    window.onresize =  null;
}
function resetAreYouSure(){
    $('.alert_box').css({
        'left': ($(window).width() - $('#event_box').width()) / 2,
        'top': ($(window).height() - $('#event_box').height()) / 2});
    $('#ajax_darkness').css({
        'width': $(window).width() + 'px',
        'height': $(document).height() + 'px'});
}
function showAreYouSure(jqueryElt, success, keepOpen){
    var okay,cancel,button_row;
    darkness = createElem('div', { id: 'ajax_darkness' });
    $(darkness).css({
        'width': $(document).width() + 'px',
        'height': $(document).height() + 'px'
    }).click(function(){
        closeAreYouSure();
    });
    box = createElem('div',{id:'event_box', className:'alert_box'});
    $(box).css({'position':'fixed'});
    $(box).click(function(e){e.stopPropagation();})
    window.onresize = resetAreYouSure;
    $(darkness).append(box);
    $('body').append(darkness);
    $(box).append(jqueryElt);
    okay = $(createElem('okay',{'type':'submit','id':'okay_button',className:'link-btn blue'},"Yes"));
    cancel = $(createElem('cancel',{'type':'submit','id':'cancel_button',className:'big-red'},"No"));

    okay.click(function(){
       success();
       if(! keepOpen){closeAreYouSure();}
    });
    cancel.click(closeAreYouSure);

    button_row = $(createElem('div',{'id':'button_row'}));
    button_row.append(okay).append(cancel);
    $(box).append(button_row);
    resetAreYouSure();
}
function showError(jqueryElt, success, keepOpen){
    var okay,button_row;
    darkness = createElem('div', { id: 'ajax_darkness' });
    $(darkness).css({
        'width': $(document).width() + 'px',
        'height': $(document).height() + 'px'
    }).click(function(){
        closeAreYouSure();
    });
    box = createElem('div',{id:'event_box', className:'alert_box'});
    $(box).click(function(e){e.stopPropagation();})
    window.onresize = resetAreYouSure;
    $(darkness).append(box);
    $('body').append(darkness);
    $(box).append(jqueryElt);
    // TODO: REBASE CHECK
    // okay = $(createElem('okay',{'type':'submit','id':'okay_button',className:'link-btn blue'},"Okay"));
    okay = $(createElem('okay',{'type':'submit','id':'okay_button',className:'big-blue'},"Okay"));

    okay.click(function(){
       success();
       if(! keepOpen){closeAreYouSure();}
    });

    button_row = $(createElem('div',{'id':'button_row'}));
    button_row.append(okay);
    $(box).append(button_row);
    $(button_row).css('text-align','center');
    resetAreYouSure();
}
function ajaxGo(dst, jsonData){
     History.pushState({
         httpReqType: "GET",
         data: jsonData,
         requestid: nextRequest()
     }, null, dst);
}

function flash(selector) {
    $(selector).css('display', 'inline-block');
    setTimeout(function(){
        $(selector).fadeOut(1500);
    }, 2000);
}

function flashMessageSent(){
    flash('#message_sent');
}

function flashMessageError(){
    flash('#message_error');
}

function flashInvitesSent(){
    flash('#invites_sent');
}

function flashInvitesError(){
    flash('#invites_error');
}

function sendFeedback(){
    $.ajax({
        url  : '/send-feedback/',
        type : 'POST',
        data : {
            'subject' : $('#contact_subject').val(),
            'message' : $('#contact_message').val(),
            'csrfmiddlewaretoken' : csrfTOKEN,
        },
        success : function(response){
            if (response == 'message sent') {
                $('#contact_subject').val('');
                $('#contact_message').val('');
                flashMessageSent();
            }
            else {
                flashMessageError();
            }
        }
    });
}

function sendInvites(){
    $.ajax({
        url  : '/send-invites/',
        type : 'POST',
        data : {
            'emails' : $('#contact_invites').val(),
            'csrfmiddlewaretoken' : csrfTOKEN,
        },
        success : function(response){
            if (response == 'invites sent') {
                $('#contact_invites').val('');
                flashInvitesSent();
            }
            else {
                flashInvitesError();
            }
        }
    });
}

function loginRequired(){
  $('#loginErrorMessage').text("Please login or signup to continue").show();
  $('#id_email').focus();
  //window.location = '/join/?requires_login=1';
}

function isOnOwnProfile(){
    if (!$('input#profile_uid').length){
        return false;
    } else {
        if ($('input#profile_uid').val() === $('input#user_uid').val()){
            return true;
        }
    }
    return false;
}

function capitaliseFirstLetter(string)
{
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function change_account_type(type){
  type = type.toLowerCase();
  console.info('change_account_type=', type);
  if (type == 'artist'){
    $('#acctype-sel li a#artist').addClass('active');
    $('[forbands]').hide();
    $('[forvenues]').hide();
    $('[forfans]').hide();
    $('[formusicians]').show();
    $('[forlabels]').hide();
    $('[name="genres"]').show();
    $('[name="instruments"]').show();
  } else if (type == 'fan'){
    $('#acctype-sel li a#fan').addClass('active');
    $('[forbands]').hide();
    $('[forvenues]').hide();
    $('[forfans]').show();
    $('[formusicians]').hide();
    $('[forlabels]').hide();
    $('[name="genres"]').hide();
    $('[name="instruments"]').hide();
  } else if (type == 'venue'){
    $('#acctype-sel li a#venue').addClass('active');
    $('[forbands]').hide();
    $('[forvenues]').show();
    $('[forfans]').hide();
    $('[formusicians]').hide();
    $('[forlabels]').hide();
    $('[name="genres"]').show();
    $('[name="instruments"]').show();
  } else if (type == 'band'){
    $('#acctype-sel li a#band').addClass('active');
    $('[forbands]').show();
    $('[forvenues]').hide();
    $('[forfans]').hide();
    $('[formusicians]').hide();
    $('[forlabels]').hide();
    $('[name="genres"]').show();
    $('[name="instruments"]').show();
  } else if (type == 'label'){
    $('#acctype-sel li a#label').addClass('active');
    $('[forlabels]').show();
    $('[forbands]').hide();
    $('[forvenues]').hide();
    $('[forfans]').hide();
    $('[formusicians]').hide();
    $('[name="genres"]').show();
    $('[name="instruments"]').show();
  } else{
    $('[forbands]').hide();
    $('[forvenues]').hide();
    $('[forfans]').hide();
    $('[formusicians]').hide();
    $('[forlabels]').hide();
    $('[name="genres"]').show();
    $('[name="instruments"]').show();
  }
  if ($.browser.is_mobile){
    // too much to display
    $('.musician_question_text').hide();
  }
}

function update_inputs(){
  // ensure that all inputs have the same content
  /* Text */
  $('[name="biography"]').val($('[name="biography"]:visible').val());
  $('[name="influences"]').val($('[name="influences"]:visible').val());
  $('[name="experience"]').val($('[name="experience"]:visible').val());
  $('[name="goals"]').val($('[name="goals"]:visible').val());
  $('[name="genres"]').val($('[name="genres"]:visible').val());
  $('[name="instruments"]').val($('[name="instruments"]:visible').val());
  $('[name="city"]').val($('[name="city"]:visible').val());
}

function setup_suggestions(){
  $('[name="city"]:visible').autosuggest('/my-account/location-ajax/'); /* Setup autosuggest for Where in the world... */
  /* Pull local autocomplete lists for genres and instruments */
  $.get('/get-autocomplete/', {
    info: '["instruments", "genres"]'
  }, function(data){
    $('[name="instruments"]:visible').localsuggest(data.instruments, { commas: true});
    $('[name="genres"]:visible').localsuggest(data.genres, { commas: true});
  });
}


