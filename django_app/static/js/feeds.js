(function(){
    /*infinite_search: whether or not to do an endless scroll callback
    inAjaxCall: whetehr or not we are currently waiting on the server to serve us some json
    inAjax call is necessary because if we switch out of "music" and then back in, we could have
    an ajax call about to return, and we dont want to call another one.
    */
    var infinite_search, inAjaxCall = false;
    infinite_search = true;
    function updateFeedsAjax(){
        $(".loader").show();
        $(".status").text("loading");
        $(".music_content").html("");
        getFeedsData(addMoreFeeds);
    }

    function getFeedsData(success, more){
        if(inAjaxCall){console.log('already in an ajax call!'); return ;}
        var time, price, location, genre,ranking,stop,start;
        time = time_dropdown.selection || 'Week';
        price = price_dropdown.selection || 'All Prices';
        ranking = ranking_dropdown.selection || 'Hottest';

        //if the values are either the default ("Location" or "Genres") or they're undefined (not logged in), send ""
        location = $('#Location').val() === 'Location' || !$("#Location").val() ? '' : $('#Location').val();
        genre = $('#Genres').val() === 'Genres' || !$("#Genres").val() ? '' : $('#Genres').val();
        if(more)
        {
            start = Math.max($("#feedsPage #artists .music.listing").length, $("#feedsPage #albums .music.listing").length, $("#feedsPage #songs .music.listing").length);
            console.log(start);
            stop = start + 10;
        }
        else{start = 0; stop = 10;}

        $('.loader .spinner').show();
        $('.box .empty').hide();

        inAjaxCall = true;
        $.ajax({
          type: 'GET',
          dataType: 'json',
          url: '/music/update-ajax',
          data: {
                'time' : time,
                'price' : price,
                'location' : location,
                'ranking' : ranking,
                'genre' : genre,
                'start' : start,
                'stop':stop
                },
          //data in this case is a json object with the following format
          //data = [logged_in , [json_artists], [json_albums], [json_songs]]
          success: function(data){
           success(data);
           inAjaxCall = false;
        },
        error: function(data){
            infinite_search= false;
        }
    });
    }

    window.prettyAppend = function(htmlList, $target, callback, doneCallback) {
      // Takes a list of HTML objects as strings
      // Appends them to target one at a time, with small delay between each
      // and fade-in effect. Just looks nice. :)

      if (htmlList.length == 0) return;

      var $rendered = $(htmlList[0]), counter = 0,
          images = $rendered.find('img'), waitUntil = images.length

      $(images).each(function(){
        $(this).on('load error', function(){
          ++ counter;
          if (counter == waitUntil){
            // Recursion happens after all images have been loaded so the transition looks nice.
            $rendered.animate({ opacity: '1' }, 70);
            var $play_button = $rendered.find('.song-play-button');
            if ($target[0].id == 'albums') {
              //bindPlayAlbum($play_button);
            } else {
              //bindPlaySong($play_button);
            }
            if (typeof callback !== "undefined") {
              callback($rendered);
            }
            if (htmlList.length > 1) {
              prettyAppend(htmlList.splice(1), $target, callback, doneCallback);
            } else if (typeof doneCallback !== "undefined"){
              doneCallback();
            }
          }
        });
      });

      $target.append($rendered);
      $rendered.css("opacity", '0');
      //$rendered.find('button.fan, button.unfan').each(function(){ $(this).fanbutton() });
      setupLinks();
      //setupDownloadButtons();

    }


    function addMoreFeeds(data){

        var artists = data[1];
        var albums = data[2];
        var songs = data[3];

        $('.loader .spinner').hide();

        if (artists.length > 0){
          prettyAppend(artists, $('#artists'));
          $('#artists_box .empty').hide();
        } else {
          if ($('#artists_box .music.listing').length == 0){
            $('#artists_box .empty').show();
          }
        }

        if (albums.length != 0){
          prettyAppend(albums, $('#albums'));
          $('#albums_box .empty').hide();
        } else {
          if ($('#albums_box .music.listing').length == 0){
            $('#albums_box .empty').show();
          }
        }

        if (songs.length != 0){
          prettyAppend(songs, $('#songs'));
          $('#songs_box .empty').hide();
        } else {
          if ($('#songs_box .music.listing').length == 0){
            $('#songs_box .empty').show();
          }
        }
        infinite_search = true;

      return;


         if($('.infinite_scrolling.feeds').length < 1){return ;}
            var parsed = data,
            item,i,max,num,stats,playLink,d,downLink,logged_in,a,reviews,reviews_button,reviews_button_div,table,
            display_price, download_button, download_button_div,download,artist_box,album_box,song_box, e;
            artist_box = $('#feedsPage #artists');
            album_box = $('#feedsPage #albums');
            song_box = $('#feedsPage #songs');
            $(".status").text("top");
            $(".loader").hide();
            logged_in = parsed[0];
            //iterate through elements (artists,albums,songs)

            //ARTISTS FIRST
            i=$("#artists .item").length + 1;
            parsed[1].forEach(function(artist) {//go through artists
                item = $(createElem('div', { className: 'item' }));
                //index
                item.append(createElem('h2',{},String(i)));
                //image
                a = $(createElem('a', {'href':artist.url})).append(createElem('img',{'src':artist.sqr_path}));
                item.append(a);
                //name
                item.append($(createElem('a', {'href':artist.url})).append(createElem('h3',{},artist.name)));
                //stats
                table = $(createElem('table',{}));
                stats = $(createElem('tr',{ className: 'stats'}));
                table.append(stats);

                if(artist.top_song_id !== -1){
                    playLink = $(createElem('a', {id:"play_song"+artist.top_song_id,'href':'/feeds/?media=songs', className:'ajax playSong'}));
                    playLink.attr('songID', artist.top_song_id);
                    playLink.append(createElem('div',{className:'song-play-button'}));
                    stats.append($(createElem('td',{className:'feeds_play'})).append(playLink));
                }


                //REVIEW BUTTON
                reviews = createElem('td', {className: 'feeds_review'});
                reviews_button_div = createElem('div', { className: 'song_reviews_button' }, 'review');
                $(reviews).append(reviews_button_div);
                $(reviews_button_div).click(function(){
                    openReviewsLightbox('profile', artist.id);
                });
                stats.append(reviews);
                if(logged_in){//display stats n such cause user logged in
                        d = small_fan_button(artist.fand, 'profile', artist.id);
                        console.log(artist.fanned);
                }
                //if user is not logged in
                else{//TOOLTIP telling users they can't use functions without registering
                    d = $(createElem('div',{className : "small_fan_button"},'FAN'));
                    e = $(createElem('div',{className : "tooltip_description"})).text('Log in or register to fan {{artist.name}}!').css({'display':'none'});
                    d.append(e);
                }
                stats.append($(createElem('td')).append(d));
                item.append(stats);

                artist_box.append(item);
                i = i + 1;
            });


            i=$("#albums .item").length+ 1;
            parsed[2].forEach(function(album) {
                item = $(createElem('div', { className: 'item' }));
                //index
                item.append(createElem('h2',{},String(i)));
                //image
                //item.append($(createElem('a',{'href':album.url})).append(createElem('img',{'src':album.image})));
                item.append($(createElem('img',{'src':album.small_cover})));
                //name
                item.append($(createElem('a',{'href': album.artist.url + "/?albumid="+album.id }, album.title)).addClass('linked_album_title'));
                item.append($(createElem('p',{})).append(createElem('a', {'href':album.artist.url},album.artist.name)));
                //stats
                table = $(createElem('table',{}));
                stats = $(createElem('tr',{ className: 'stats'}));
                table.append(stats);

                playLink = $(createElem('a', {id:"play_album"+album.id,'href':'/feeds/?media=albums', className:'ajax playAlbum '+album.id}));
                playLink.append(createElem('div',{className:'song-play-button'}));
                stats.append($(createElem('td',{className:'feeds_play'})).append(playLink));

                if(logged_in){
                    //download button
                    download = createElem('td',{className:'feeds_download'});

                    if (album.download_type !== 'none') {
                        download_button = createElem('a',  { className: 'ajax downloadAlbum ' + album.id });
                        download_button_div = createElem('div', { className: 'song_download_button' }, album.pretty_price);
                        $(download).append(download_button);
                        $(download_button).append(download_button_div);
                    }

                    stats.append(download);
                    d = small_fan_button(album.fanned, 'album', album.id);

                }
                else{//for non logged in users
                    d = $(createElem('div',{className : "small_fan_button"},'FAN'));
                    e = $(createElem('div',{className : "tooltip_description"})).text('Log in or register to fan {{album.title}}!').css({'display':'none'});
                    d.append(e);
                }
                //review button
                reviews = createElem('td', {className: 'feeds_review'});
                reviews_button_div = createElem('div', { className: 'song_reviews_button' }, 'review');
                $(reviews_button_div).click(function(){
                    openReviewsLightbox('album', album.id);
                });
                $(reviews).append(reviews_button_div);
                stats.append(reviews);


                stats.append($(createElem('td')).append(d));
                item.append(stats);
                album_box.append(item);
                i = i + 1;
            });

            i=$("#songs .item").length+ 1;
            parsed[3].forEach(function(song) {
                item = $(createElem('div', { className: 'item' }));
                //index
                item.append(createElem('h2',{},String(i)));

                //item.append($(createElem('a',{'href':song.url})).append(createElem('img',{'src':song.image})));
                item.append($(createElem('img',{'src':song.artist.sqr_path})));

                //name
                item.append($(createElem('h3',{},song.title)));
                item.append($(createElem('p',{})).append(createElem('a', {'href':song.artist.url},song.artist.name)));
                //stats
                table = $(createElem('table',{}));
                stats = $(createElem('tr',{ className: 'stats'}));
                table.append(stats);

                //play button

                playLink = $(createElem('a', {id:"play_song"+song.id,'href':'/feeds/?media=songs', className:'ajax playSong'}));
                playLink.attr('songID', song.id);
                playLink.append(createElem('div',{className:'song-play-button'}));
                stats.append($(createElem('td',{className:'feeds_play'})).append(playLink));



                if(logged_in){
                    //download button
                    download = createElem('td',{className:"feeds_download"});
                    if (song.download_type !== "none"){
                        download_button = createElem('a',  { className: 'ajax downloadSong ' + song.id });
                        download_button_div = createElem('div', { className: 'song_download_button' }, song.pretty_price);
                        $(download).append(download_button);
                        $(download_button).append(download_button_div);
                    }
                    stats.append(download);

                    d = small_fan_button(song.fanned, 'song', song.id);


                }
                else{//not logged in users
                    //playLink = $(createElem('li',{className:'play',title:'login or register to play music!'}));
                    d = $(createElem('div',{className : "small_fan_button"},'FAN'));
                    e = $(createElem('div',{className : "tooltip_description"})).text('Log in or register to fan {{song.title}}!').css({'display':'none'});
                    d.append(e);

                    //stats.append(playLink);
                }

                reviews = createElem('td', {className: 'feeds_review'});
                reviews_button_div = createElem('div', { className: 'song_reviews_button' }, 'review');
                $(reviews).append(reviews_button_div);
                $(reviews_button_div).click(function(){
                    openReviewsLightbox('song', song.id);
                });

                stats.append(reviews);
                stats.append($(createElem('td')).append(d));
                item.append(stats);

                song_box.append(item);
                i = i + 1;
            });
                if(parsed[1].length + parsed[2].length + parsed[3].length > 0){
                    max = Math.max($("#artists").height(), $("#songs").height(), $("#albums").height());
                    if($(window).height() > $("#filters-container").height() + max + 100 ){
                        getFeedsData(addMoreFeeds,'t');
                    }
                }
            setupPlayer();
    }
    /*
        ajax call that updates feeds based on filters
        and refreshes the information on the page
        called from a change in forms in the feeds template
        calls update_ajax() in feeds.views.py
    */


    /*
        called when the feeds template is onready()
        sets up feeds by styling all the filters
        and calling updateFeedsAjax()
    */
    function setupFeeds(){
        window.ranking_dropdown = new filter_dropdown('Ranking',
            function(){
                if(ranking_dropdown.selection == "Newest"){
                    $("#time_filter_module").hide();
                }else{
                    $("#time_filter_module").show();
                }
                updateFeedsAjax();
            }, 150);

        $('#rank_filter_module').append(ranking_dropdown.all);
        ranking_dropdown.set_items(['Hottest','Newest']);

        window.time_dropdown = new filter_dropdown('Time', function(){ updateFeedsAjax(); });
        $('#time_filter_module').append(time_dropdown.all);
        time_dropdown.set_items( ['All Time','Today', 'Week', 'Month', 'Year'] );
        window.price_dropdown = new filter_dropdown('Price', function(){ updateFeedsAjax(); });
        $('#price_filter_module').append(price_dropdown.all);
        price_dropdown.set_items( ['All Prices','Free', 'NYP', 'Paid', 'No Download'] );

        $('button#filter').click(function() { updateFeedsAjax();});

        $('.filter_module input:text').each(function() {
          $(this).typeaction(updateFeedsAjax);
        });

        updateFeedsAjax();

        $('.auto_update').change(function () {
            updateFeedsAjax();
        });
        //setup feeds autocomplete

        autocompleteAll({
            '#Genres' : 'genres' ,
            '#Location' : 'locations'
        }, updateFeedsAjax);

        $(window).endlessScroll({
            bottomPixels:      500,  //aggressive preloading
            intervalFrequency: 100,  //sensitive trigger
            fireOnce:          true, //i think?
            fireDelay:         0,
            loader:            '',//'<img src="/public/images/ajax-loader.gif" alt="loading..."/>',
            ceaseFire: function(page){
              if($('.infinite_scrolling.feeds').length < 1){
                return true;
              }
              return false;
            },
            resetCounter: function(page) { return ; },
            callback: function(page){
                if(infinite_search){
                  infinite_search = false;
                  getFeedsData(addMoreFeeds,'t');
                }
                else{ console.log('waiting'); }
            }
        });

    }
window.updateFeedsAjax = updateFeedsAjax;
window.setupFeeds = setupFeeds;
window.getFeedsData = getFeedsData;
window.addMoreFeeds = addMoreFeeds;

}());
