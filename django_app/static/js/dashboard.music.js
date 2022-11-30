 /*global
  hearo,
  */

(function(){
  var setup = function(){


  // show for when user edits song and album titles
  hearo.elements.savebutton.show();

  /*
   * jQuery objects
   */

  /* Artist agreement objects */
  var $artist_agreement = $('#sign_agreement'),
  $agreed = $('input#artist_agreement'),
  $line1 = $('#add_line1'),
  $line2 = $('#add_line2'),
  $city = $('#add_city'),
  $state = $('#add_state'),
  $zip = $('#add_zip'),
  $country = $('#add_country'),
  $i_agree = $('#i_agree'),
  /* Non-album music box */
  $nonalbum = $('#nonalbum'),
  /* Save button */
  $save_button = $('button#save'),
  /* Upload hint */
  $hideonupload = $('[hideonupload]'),
  $showonupload = $('[showonupload]')
  ;

  /*
   * Helper methods
   */

  var get_file_type = function(file){
    if (file.type !== ''){
      return file.type;
    } else {
      /* Match for a period and three or four characters at the end of the string */
      var extension = file.name.match(/\.....?$/g);
      if (extension.length !== 0){
        return extension[0].substring(1);
      } else {
        return 'UNKNOWN TYPE'; }
    }
  }


  var setup_price_input = function($this){
    var validate = function(){
      var val = $this.val(), groups = val.match(/\d+/g);
      /* Add decimals */
      if (groups.length == 1) {
        if (parseInt(val, 10) >= 10){
          $this.val('9.99');
        } else {
          var val = groups[0][0];
          $this.val(val + '.00');
        }}
    };

    $this.whitelist(/[\d\.]/g).blur(validate).enter(function() {
      validate();
      $this.blur();
    });

    $this.click(function(){
      $this.select();
    }).focus(function(){
      $('label[for="' + this.id + '"]').addClass('focused');
    }).blur(function(){
      $('label[for="' + this.id + '"]').removeClass('focused');
      var songid = $this.attr('songid');
      var albumid = $this.attr('albumid');
      if (songid){
        post_song_detail(songid, {
          price: $this.val()
        });
      } else if (albumid){
        post_album_detail(albumid, {
          price: $this.val()
        });
      }
    });
  };

  /* Animate song listing when deleted */
  var song_deletion_animation = t = function($listing){
    var $table = $listing.closest('#songs'), tn = parseInt($listing.attr('tracknum'), 10),
    $below = $table.find('.song.listing[tracknum="' + (tn + 1) + '"]');
    $listing.animate({ opacity: 0 }, 100, 'easeOutQuad');
    setTimeout(function() {
      $listing.hide();
      $below.css({ 'margin-top': '41px' })
      .animate({ 'margin-top': 0 }, 300, 'easeOutQuad');
      setTimeout(function(){
        $listing.remove();
        redo_tracknums($table);
      }, 300);
    }, 100);
  };


  /*
   * When user starts dragging a song listing do a quick 3-frame anim
   * of it moving up a bit off the page and getting a shadow.
   */

  var animate_song_listing_lift = function($listing, i){
    if (i == 3) return;
    var l = ['a','b','c'];
    $listing.removeClass(l[i-1] || '').addClass(l[i]).animate({ top: '-=3px' }, 0);
    setTimeout(function(){
      animate_song_listing_lift($listing, i+1);
    }, 50);
  };


  /* Don't stack up animations if user drags song around too fast. */
  var drop_space_being_animated = false;

  var make_drop_space = function(e, moved, $content){
    var $l, $chosen = null, $draggee = $(e.target), draggee_offset = $draggee.offset();


    if ($content === null){
      return;
    }

    /*
     * There's some bug where sometimes the target is the songs list
     * that's being dragged. Catch that and don't entertain it.
     */
    if (e.target.className !== 'sl-grip'){
      return $content.find('.song.listing').last();
    }

    if (moved.y > 0){
      $content.find('.song.listing:not(.lifted)').each(function(i, l){
        $l = $(l), offset = $l.offset();
        var difference = draggee_offset.top - offset.top;
        if (difference > -20 && difference < 40){
          make_gap($l);
          $chosen = $l;
          /* Stop looking */
          return false;
        }
      });
    } else if (moved.y < 0){
      $content.find('.song.listing:not(.lifted)').each(function(i, l){
        $l = $(l), offset = $l.offset();
        var difference = draggee_offset.top - offset.top;
        if (difference < 60 && difference > 0){
          make_gap($l);
          $chosen = $l;
          /* Stop looking */
          return false;
        }
      });
    } else {
      return null;
    }
    return $chosen;
  };


  var get_abs_xy = function(e){
    var x = e.clientX + window.scrollX,
    y = e.clientY + window.scrollY;
    return {x: x, y: y};
  }

  var nudge_window = n = function(i){
    if (i === undefined) i = 100;
    if (Math.abs(i) < 1) return;
    scroll_window(i);
    setTimeout(function(){
      nudge_window(i * 0.7);
    }, 3);
  }

  var scroll_window = function(amt){
    /*
     * Takes number, scrolls that much down and adjusts .lifted song listing
     * Give negative to scroll up.
     */

    /* Don't do anything if the scroll has maxed out in either direction. */
    if (amt < 0 && window.scrollY == 0) return;
    if (amt > 0 && (window.scrollY + window.innerHeight) == document.height) return;

    window.scrollTo(0, window.scrollY + amt);
  }

  var get_drop_target = function(coords){
    var $target = null;
    $('div.content[droptarget]').each(function(){
      var $this = $(this), position = $this.offset(),
      height = $this.outerHeight();
      if (coords.y > position.top && coords.y < position.top + height){
        $target = $this;
        return false;
      }
    });
    return $target;
  };

  /* Take a song listing DOM object, bind listeners to its UI */

  var bind_song_listing_events = function($listing){
    /*
       Takes a .song.listing, sets up its dynamic UI
       Kind of a monster function. Sorry.
       */
    var download_types = {
      'paid only': 'none',
      '1st stream': function(){
        return $listing.find('.pricing input:checkbox.nyp').is(':checked') ? 'name_price' : 'normal'
      }
    }, reset, songid = $listing.attr('songid');

    /* Download type earl slider */
    $listing.find('ul.earl')
    .css({
      display: 'inline-block'
    }).earl({
      padding: 6,
      callbacks: {
        userselect: function(selection){
          var $controls = $listing.find('.pricing .price-controls, .pricing .nyp-opt');
          /* Save song download type selection */
          if (selection === "1st stream"){
            $controls.uncloak(200);
          } else {
            $controls.cloak(200);
          }
          post_song_detail(songid,
                           { download_type: download_types[selection]
                           });}
      }
    });

    /* Name editing */
    $listing.find('.sl-name button').inline_edit_button(
      $listing.find('.sl-name div'),
      function(val){
        post_song_detail(songid, { title: val });
      }
    );

    /* Name Your Price toggling */
    $listing.find('.pricing input:checkbox.nyp').change(function(){
      var $this = $(this), $controls = $listing.find('.price-controls'),
      $label = $controls.find('label.right-half'),
      $input = $controls.find('input.inline-edit');

      if ($this.is(':checked')){
        /* Change the price to Name Your Price */
        $label.show();
        $input.removeClass('right-half').addClass('middle');
        post_song_detail(songid, { download_type: 'name_price' });
      } else {
        /* Change the price to normal (set price) */
        $label.hide();
        $input.removeClass('middle').addClass('right-half');
        post_song_detail(songid, { download_type: 'normal' });
      }
    });

    $listing.find('button.delete').click(function(){
      $.ajax({
        type: 'POST',
        url: '/my-media/delete-song/',
        data: {
          songid: parseInt(songid, 10),
          csrfmiddlewaretoken: csrfTOKEN
        },
        dataType: 'json',
        success: function(){
          song_deletion_animation($listing);
        }
      });
    });

    $listing.find('.pricing .price-controls input.inline-edit').each(function(){
      setup_price_input($(this));
    });


    /* Make the UI go into minimal mode when dragging a song. */
    /*

    Disabled for now

    var drag_mode_ui = function(){
      var $hide = $('.music-uploader, #create-album')
          $album_infos = $('div.album-info');

      $hide.collapse();

      $album_infos.each(function(){
        var $this = $(this);

        $this.animate({ height: '100px' }, 200, 'easeOutExpo')
        .find('div.cover')
        .animate({ width: '100px' }, 200, 'easeOutExpo')
        .children().first().css({
          '-webkit-transform': 'scale(0.5)',
          'margin-left': '-50px',
          'margin-top': '-50px'
        });
        $this.find('.upload-cover').hide();
        $this.find('.info').animate({ width: '856px' }, 200, 'easeOutExpo');
      });

      return function(){
        $hide.uncollapse();

        $album_infos.each(function(){
          var $this = $(this);

          $this.animate({ height: '200px' }, 200, 'easeOutExpo')
          .find('div.cover')
          .animate({ width: '200px' }, 200, 'easeOutExpo')
          .children().first().css({
            '-webkit-transform': '',
            'margin-left': '',
            'margin-top': ''
          });
          $this.find('.upload-cover').show();
        $this.find('.info').animate({ width: '756px' }, 200, 'easeOutExpo');
        });
      };
    };
    */

    /* Drag and drop */
    $listing.find('.sl-grip').mousedown(function(e){
      var $lifted = $listing.lift(e), $content = $listing.closest('.content'),
      $songs = $content.find('.song-listings'),
      $uploader = $content.find('.music-uploader'), uploader_height = $uploader.outerHeight(),
      $droptarget, $on_top_of, scroll_interval, reset_ui;

      $listing.hide();

      $('#songs').animate({ 'margin-bottom': '+=41px' }, 0);
      $('.music-uploader').cloak(200);
      animate_song_listing_lift($lifted, 0);

      // Disabled for now. Don't touch.
      // reset_ui = drag_mode_ui();

      /* Drag and drop for song listings. FAT block of code. */
      $lifted.addClass('lifted').draggable({
        autoPosition: false,
        boundaryParent: null,
        initiator: $lifted.find('.sl_grip'),
        startRightAway: true,
        callbacks: {
          mouseup: function(e){

            /* Which container are we dropping into? */
            $droptarget = get_drop_target(get_abs_xy(e));
            /* Scrap the lifted song listing clone and  */
            $lifted.remove();
            $listing.show().removeAttr('lifted');

            /* Fix a minor bug that comes up randomly */
            setTimeout(function(){
              $('.song.listing:not(.lifted)').css({ top: 0 });
            }, 5);

            /* Drop it in the right spot! */
            if ($droptarget == null){
              /* Put it back if the drop it right away */
              reorder_songs($listing, $listing, $content.find('.album.listing'));
            } else {
              if ($on_top_of !== undefined){
                if (!$droptarget.has($on_top_of).length){
                  $on_top_of = $droptarget.find('.song.listing:not([lifted])').last();
                }
                /* Redo tracknums of old and new home. */
                redo_tracknums($droptarget);
                redo_tracknums($content);


                $on_top_of.after($listing);
                reorder_songs($listing, $on_top_of, $droptarget);
              }
            }

            /* Reset UI */
            clearInterval(scroll_interval);
            //reset_ui();
            $('#songs').animate({ 'margin-bottom': '-=41px' }, 0);
            $('.music-uploader').uncloak(200);

          },
          move: function(e, moved){
            var coords = get_abs_xy(e);

            if ((window.innerHeight - e.clientY) < 150 && scroll_interval == null){
              scroll_interval = setInterval(function(){
                scroll_window(20)}, 4);
            } else if (e.clientY < 150 && scroll_interval == null){
              scroll_interval = setInterval(function(){
                scroll_window(-20)}, 4);
            } else {
              clearInterval(scroll_interval);
              scroll_interval = null;
            }

            $droptarget = get_drop_target(coords);


            if (drop_space_being_animated) {
              return false;
            } else {
              var ot = make_drop_space(e, moved, $droptarget);
              if(ot != undefined){
                $on_top_of = ot;
              }
            }
          }
        }
      });
    });
  }


  var bind_album_listing_events = function($listing){
    /*
       Takes an .album.listing, sets up its dynamic UI
       */
    var albumid = parseInt($listing.attr('albumid'), 10),
    $price_controls = $listing.find('.info .price-controls, .info .nyp-opt');

    /*
    $listing.find('.availability ul.earl').earl({
      padding: 6,
      callbacks: {
        userselect: function(selection){
          var download_types = {
            'Stream only': 'none',
            'Downloadable': function(){
              return $listing.find('.info .pricing input:checkbox.nyp').is(':checked') ? 'name_price' : 'normal'
            }
          }, $controls = $listing.find('.pricing .price-controls, .pricing .nyp-opt, .song.listing .sl-dltype');

          // Save song download type selection
          if (selection === "Downloadable"){
            $controls.uncloak(200);
          } else {
            $controls.cloak(200);
          }
        }
      }
    });
    */

    $listing.find('.pricing .price-controls input.inline-edit').each(function(){
      setup_price_input($(this));
    });

    $listing.find('input:checkbox.downloadable').change(function(){
      var $this = $(this);
      if ($this.is(':checked')){
        $price_controls.uncloak(200);
        post_album_detail(albumid,
                          { download_type: function(){
                            return $listing.find('.info .nyp-opt input:checkbox').is(':checked') ? 'name_price' : 'normal'
                          }()});
      } else {
        $price_controls.cloak(200);
        post_album_detail(albumid, { download_type: 'none' });
      }
    });

    $listing.find('input:checkbox.nyp').change(function(){
      var $suggested = $listing.find('.info .price-controls label.right-half'),
      $input = $listing.find('.info .price-controls input:text');
      if ($(this).is(':checked')){
        post_album_detail(albumid, { download_type: 'name_price' });
        $suggested.show();
        $input.removeClass('right-half').addClass('middle');
      } else {
        post_album_detail(albumid, { download_type: 'normal' });
        $suggested.hide();
        $input.addClass('right-half');
      }


    });

    $listing.find('input.cover-upload').change(function(){
      var $this = $(this), data = new FormData(),
      $container = $this.closest('.cover-image-div'), $hover_target = $this.closest('.upload-cover');

      data.append('cover_file', this.files[0]);
      data.append('albumid', albumid);
      data.append('csrfmiddlewaretoken', csrfTOKEN);
      $container.removeClass('hover-show').find('[deleteonupload]').remove();
      var undo = $this.parent().button_spin();

      $.ajax({
        type: 'POST',
        url:  '/my-media/upload-album-cover/',
        data: data,
        success: function(response){
          var i = new Image;
          /* Wait until we've actually loaded the desired small-sized cover before changing anything. */
          i.onload = function(){
            this.files = [];
            undo();
            $container.css({
              background: 'url("' + this.src + '")'
            });
            $container.addClass('hover-show');
            $hover_target.addClass('hover-show-target');
            $this.parent().find('span').text('Change album cover');
          };
          i.src = response.path;
          /* Reset the button for more action */
        },
        cache: false,
        dataType: 'json',
        contentType: false,
        processData: false
      });
    });

    $listing.find('p.album-title button').inline_edit_button(
      $listing.find('p.album-title span'),
      function(val){
        post_album_detail(albumid, { title: val });
      });

      /* Given a year, make sure it's between 1950 and now */
      var validate_year = function(year){
        year = parseInt(year, 10);
        if (year < 1950){
          year = 1950;
        }
        var now = 1900 + new Date().getYear();
        if (year > now){
          year = now;
        }
        return year;
      }

      $listing.find('p.album-year button')
      .inline_edit_button($listing.find('p.album-year span.year'),
        function(val){
          post_album_detail(albumid, { year_released: validate_year(val) });
        },
        function($input){
          $input.whitelist(/\d/).blur(function(){
            $input.val(validate_year($input.val()));
          });
        });

      $('.error').remove();
      bind_upload_button_handler($listing.find('.music_upload_input'));

      $listing.find('.info button.delete').click(function(){
        $.ajax({
          type: 'POST',
          url: '/my-media/delete-album/',
          data: {
            albumid: parseInt($listing.attr('albumid'), 10),
            csrfmiddlewaretoken: csrfTOKEN
          },
          dataType: 'json',
          success: function(){
            $listing.parent().collapse();

    }});});} // End of bind_album_listing_events



    var prepend_song_listing = function(html, $target){
      /* Add a song listing to the top of a list, be it non-album section or an album */
      var $listing = $(html);
      $target.find('.pending').after($listing);
      bind_song_listing_events($listing);
      redo_tracknums($target);
    };

    /*
     * Given a div element containing song listings, sets their tracknums incrementally
     * starting at the top, with 0 (for the pending listing).
     */
    var redo_tracknums = function($table){
      var tn = 0;
      $table.find('.song.listing').each(function(i, el){
        $(el).attr('tracknum', tn);
        tn ++;
      });
    };

    var reorder_songs = function($song, $on_top_of, $droptarget){
      /* Reorder songs on client side, then tell the server what has happened. */
      hearo.elements.savebutton.spin();

      var albumid = $droptarget.children().first().attr('albumid');
      if (albumid == undefined){
        albumid = 0;
      } else {
        albumid = parseInt(albumid, 10);
      }

      var n = parseInt($on_top_of.attr('tracknum')) + 1;

      console.info('n=', n);

      $.ajax({
        type: 'POST',
        url: '/reorder-songs/',
        data: {
          songid: $song.attr('songid'),
          albumid: albumid,
          csrfmiddlewaretoken: csrfTOKEN,
          n: n
        },
        dataType: 'json',
        success: function(data) {
          $.each(data, function(i, val){
            $.each(val, function(id, tn){
              $('.song.listing[songid="' + parseInt(id, 10) + '"]').attr('tracknum', parseInt(tn, 10));
            });
          });
        },
        complete: function(data){
          hearo.elements.savebutton.revert();
        }});};

    var make_gap = function(after){
      /* Make all songs after a certain song move down to indicate you can drop a song there */
      /* Don't overload the animation */
      if (drop_space_being_animated) return;

      /* tracknum, move everything with greater tracknum */
      var tracknum = after.attr('tracknum');
      drop_space_being_animated = true;

      after.parent().children().each(function(){
          var $this = $(this),
              movedown = parseInt($this.attr('tracknum'), 10) > parseInt(tracknum, 10);
          /* Move it or not! */
          $this.animate({ top: movedown ? '65px' : '0px' }, 30);
      });

      /* Let the songs shift again in a little while */
      setTimeout(function(){
        drop_space_being_animated = false;
      }, 45);};

    var get_file_size = function(file){
      /* Given a file, return its size in MB as a string */
      return (file.size / Math.pow(10, 6)).toFixed(2) + 'MB';
    }

    /* Given an array of Files, upload them one at a time biotch */

    function log_filetype_error(fn, reason){
      // I'm curious how many morons get turned down by these errors.
      // Especially the morons trying to upload MP3s.
      $.ajax({
        url: '/my-media/filetype-error/',
        type: 'POST',
        data: {
          filename: fn,
          reason: reason,
          csrfmiddlewaretoken: csrfTOKEN
        }
      });
    }

    function showError(msg, $after){
      if (typeof msg !== "string") {
        msg = "Oops! That's a server error. Please try again.";
      }
      if (msg.length === 0) return;
      if ($after == undefined){
        return;	//$after = $("#singles");
      }
      var $error = $('<div class="song listing error"></div>').append($('<div></div>').html(msg));
      $after.before($error);
    }

    var upload_music = function(files, $input, $container, badfiles){

      if (files.length === 0) return;

      var flength = files.length;

      if (typeof badfiles === 'undefined') {

	// find bad files and place them on top of the queue so we
	// can present the user this information before any uploads take
	// place + this also fixes a ui bug (bit of a hack but works)
	var badfiles = [], ext;
	$(files).each(function(i, file){
	  ext = file.name.match(/\.\w*$/gi);
	  if (file.name.length > 100){
	    badfiles.push(file)
	    files.splice(i, 1);
	  } else if (!/\.(wave?|wav?|aiff?|flac)$/gi.test(ext)){
	    badfiles.push(file)
	    files.splice(i, 1);
	  } else {
	    // Frontend compression check for WAV and AIFF
	    var isWAV  = /\.(wave?|wav?)/.test(file_extension);
	    var isAIFF = /\.aiff?/.test(file_extension);

	    if (isWAV || isAIFF){
	      var fr = new FileReader();

	      fr.onload = function(e) {
		var filedata = e.target.result, isUncompressed;

		if (isWAV){
		  isUncompressed = (filedata.indexOf("fact") == -1);
		} else if (isAIFF){
		  isUncompressed = (filedata.indexOf("AIFC") == -1);
		}

		if (!isUncompressed){
		  badfiles.push(file)
		}
	      }
	      fr.readAsText(file);
	      files.splice(i, 1);
	    }
	}});

	// fixes issue with last file appearing twice if all files are bad
	if (badfiles.length == flength){
	  files = badfiles;
	} else {
	  files = badfiles.concat(files);
	}
      }

      // take first file, use 'files.slice' after to resume uploads
      var file = files[0];

      var file_extension = file.name.match(/\.\w*$/gi);

      if (file_extension){

	if (file.name.length > 100){
	  showError(file.name + " is too long, please make sure the title is no greater than 100 characters.", $container)
	  log_filetype_error(file.name, "Title too long");
	  return upload_music(files.slice(1), $input, $container, badfiles);
	}

        file_extension = file_extension[0];

        // Make sure the file is a valid filetype
        if (!/\.(wave?|wav?|aiff?|flac)$/gi.test(file_extension)){
          showError(file.name + " seems to be a " + file_extension.substring(1).toUpperCase() + " file. Please only upload valid lossless FLAC, AIFF, or WAV files.", $container)
          log_filetype_error(file.name, "Wrong format entirely");
          return upload_music(files.slice(1), $input, $container, badfiles);
        } else {

          // Frontend compression check for WAV and AIFF
          var isWAV  = /\.(wave?|wav?)/.test(file_extension);
          var isAIFF = /\.aiff?/.test(file_extension);

          if (isWAV || isAIFF){
            // WAV of AIFF filetypes can be compressed, we can't tell from looking at the file extension or type.
            //
            // We CAN tell by reading the file, specifically its header.
            //
            // If it's a WAV, make sure it's an uncompressed WAV.
            // What we look for is the "fact" chunk which contains information
            // required to decompress a compressed file. Uncompressed, lossless WAV files
            // don't have this chunk, so simply looking for it can determine if the
            // file is lossless.
            //
            // Source: http://www.sonicspot.com/guide/wavefiles.html#fact
            //
            // With AIFF it's a similar deal, except the file header says AIFC instead of AIFF.
            // File extensions often still say AIFF, so we have to read the file header to be sure.
            //
            // Source:
            //
            // http://www-mmsp.ece.mcgill.ca/Documents/AudioFormats/AIFF/AIFF.html

            var fr = new FileReader();

            fr.onload = function(e) {
              var filedata = e.target.result, isUncompressed;

              if (isWAV){
                isUncompressed = (filedata.indexOf("fact") == -1);
              } else if (isAIFF){
                isUncompressed = (filedata.indexOf("AIFC") == -1);
              }

              if (isUncompressed){
                continue_upload(file, files, $input);
              } else {
                log_filetype_error(file.name, "Compressed " + file_extension);
                showError(file.name + " is a compressed " + file_extension.substring(1).toUpperCase() + " file. Please only upload lossless, uncompressed FLAC, AIFF, or WAV files.", $container)
                return upload_music(files.slice(1), $input, $container, badfiles);
              }
            }
            fr.readAsText(file);
          } else {
            // Good old FLACs
            continue_upload(file, files, $input, $container);
          }
        }
      }
    }

    var update_listings = function(){
      var $processing = $('.song.listing.admin.processing'),
          selectors = [],
          $all = $('.song.listing.admin'),
          all = []
          ;

      $processing.each(function(){
        selectors.push("#" + this.id);
      });

      $all.each(function(){
        all.push("#" + this.id);
      });

      if (selectors.length) {
        hearo.utils.refreshSection(all, function(){
          bind_song_listing_events($(this));
        });
      }
    }


    setInterval(function(){
      update_listings();
    }, 20 * 1000);

    var continue_upload = function(file, files, $input, $container) {
      var albumid = $input.attr('albumid');
      albumid = albumid ? albumid : "";

      var $uploadedContainer = $input.closest('.content').find('.uploaded-already');
      /* Undo method for the pending song listing, save for AJAX callback */

      var undo = show_pending_song_upload({
        filename: file.name,
        filesize: get_file_size(file),
        filetype: get_file_type(file).toUpperCase()
      }, $input.closest('.songs-container').find('.songs-list'));

      var refresh = function(){

        hearo.utils.refreshSection("#" + $uploadedContainer[0].id, function() {
          undo();
          update_listings();
          //bind_song_listing_events($(this));
        });
      }

      var direct_upload = function(recurse){
        var s3 = new S3Upload({
          file: file,
          albumid: albumid,
          s3_sign_put_url: '/get-signature/',

          onProgress : function(percentage, status){
            //console.log(percentage, status);
            $('.sl-upload-bar').val(percentage).trigger('change')
          },

          onFinishS3Put: function(public_url, data){
            if (data.hasOwnProperty('as_admin_listing')){
              $.post('/cmm-register/', {id: data.id, csrfmiddlewaretoken: csrfTOKEN}, function(){
                appended = true;
                refresh();
                /* Indicate that new song upload is finished with save spin */
                setTimeout(function(){
                  hearo.elements.savebutton.spin().revert();
                }, 100);
                upload_music(files.slice(1), $input, $container, false);
              });
            }else{
              upload_music(files.slice(1), $input, $container, false);
            }
          },

          onError: function(status, data){
              var error = "";
              if (status === 'not_supported'){
                error = 'Your browser does not support uploading!';
              }else if(status === "bad_json"){
                error = "Our servers didn't get that quite right. We're working on it!";
              }else if(status === 'xhr' || status === 403){
                //the weird xhr transfer bug
                error = "We had trouble connecting you to our servers. Please try again.";
                if(recurse > 0){
                  setTimeout(function(){
                    direct_upload(recurse - 1);
                  },250);
                  return ;
                }
              }else{
                error = "Upload Error: " + status;
              }
              showError(error, $container)
              refresh();
              if(data){
                $.post('/failed-upload/', {id: data.id, csrfmiddlewaretoken: csrfTOKEN}, function(){});
              }
              upload_music(files.slice(1), $input, $container, badfiles);
          }
        });
      }
      setTimeout(function(){
        direct_upload(0); // 0 if we arent using the recurse hack
      }, 250);
    };

    /*
     * Shows transluscent uploading song listing with spinner
     * I/P: song object with keys: filename, filesize, filetype
     *      target jQuery object, container of the pending listing we want
     * O/P: anon function that undoes this. Call when upload is done.
     */

    var show_pending_song_upload = function(song, $target){
      if ($target == undefined) $target = $('#nonalbum .songs-list');

      var $pending = $target.find('.pending'), $upload_hint = $('.upload-hint');

      $.each(['filename', 'filesize', 'filetype'], function(i, e){
        $pending.find('#' + e).text(song[e]);
      });
      /* Slide it in from the top */
      $target.animate({ 'margin-top': '0px' }, 250, 'easeOutQuad');
      /* Return anon function that undoes this */
      $hideonupload.remove();
      $showonupload.show();
      return function(){
        $target.animate({ 'margin-top': '-41px' }, 0);
      };
    };

    /*
     * Checks if the I Agree button should be lit up
     * and if the form should be submitted
     * based on if the user has given their address
     * and checked "I have read and agree..."
     */
    var check_artist_agreement_completion = function(){
      /*
       * JavaScript pattern matching lol
       * Well sort of. This is just a more
       * minimal if/else chain I just made up
       */
      return !$agreed.is(':checked') ? false :
      $line1.val().length <= 3       ? false :
      $city.val().length  <= 2       ? false :
      $country.val().length <  3     ? false : true;
    };

    /*
     * Lights up the I Agree button if the form has been
     * satisifed, dims it if it becomes unsatisfied.
     */
    var update_i_agree_button_state = function(){
      if (check_artist_agreement_completion()){
        $i_agree.removeClass('disabled');
      } else {
        $i_agree.addClass('disabled');
      }
    }

    /*
     * Ditches the artist agreement and reveals the music upload view.
     */
    var hide_artist_agreement = function(){
      $artist_agreement.animate({ opacity: 0 }, 100);
      setTimeout(function(){
        $('[hideonagreement]').hide().remove();
        $('[showonagreement]').show().animate({ opacity: 1 }, 300);
      }, 100);
    };

    /*
     * AJAX call to submit the artist agreement form
     */
    var submit_artist_agreement = function(){
      if (check_artist_agreement_completion()){
        var undo = $i_agree.button_spin();
        $.ajax({
          type: 'POST',
          url: '/my-account/private-location-ajax/',
          data: {
            csrfmiddlewaretoken: csrfTOKEN,
            address1: $line1.val(),
            address2: $line2.val(),
            city:     $city.val(),
            state:    $state.val(),
            zip:      $zip.val(),
            country:  $country.val()
          },
          success: hide_artist_agreement,
          error: function () {
            undo();
            $("#error-info-message").show();
          }
        });
      } else {
        return false;
      }
    };

    /*
     * Makes AJAX call to create a new album, returns the rendered template and appends it to the DOM.
     */
    var create_new_album = function(e){
      var undo = $(e.target).button_spin(), $albums = $('.album.listing');

      if ($albums.length === 0){
        $('[hideonfirstalbum]').collapse();
        $('[showonfirstalbum]').fadeIn(200);
      }

      $.ajax({
        type: 'POST',
        url: '/my-media/create-album/',
        data: { csrfmiddlewaretoken: csrfTOKEN },
        dataType: 'json',
        success: function(response){
          undo();
          var $album = $(response.html);
          $album.cloak(0);
          $('#create-another-album').after($album);

          var height = $album.outerHeight();
          $album.css({
            height: '0px'
          }).animate({
            height: height
          }, 200);

          setTimeout(function(){
            $album.css({ height: 'auto' });
          }, 200);

          setTimeout(function(){
            bind_album_listing_events($album.children().first());
            $album.uncloak(300);
          }, 100);
        }
      });
    };

   /*
    * Bind event handlers
    */

    var bind_upload_button_handler = function($input){
      $input.change(function(){
        var files = [];
	console.info('once');
        $.each(this.files, function(){
          files.push(this);
        });
	var $target = $input.closest('.songs-container');
        upload_music(files, $input, $target);
        /* Clear the FileList */
        this.value = '';
      });
    }


    var post_song_detail = function(songid, post_data){
      var data = $.extend({
        csrfmiddlewaretoken: csrfTOKEN,
        id: parseInt(songid, 10)
      }, post_data);

      hearo.elements.savebutton.spin();

      $.ajax({
        type: 'POST',
        url: '/my-media/song-details/',
        data: data,
        complete: function(d){
          hearo.elements.savebutton.revert();
        }
      });
    };

    var post_album_detail = function(albumid, post_data){
      var data = $.extend({
        csrfmiddlewaretoken: csrfTOKEN,
        id: parseInt(albumid, 10)
      }, post_data);

      hearo.elements.savebutton.spin();

      $.ajax({
        type: 'POST',
        url: '/my-media/album-details/',
        data: data,
        complete: function(d){
          hearo.elements.savebutton.revert();
        }
      });
    };


    /*
     * Since everything is autosaved on this view, let the user click the save button
     * but don't actually do anything. :)
     */

    $save_button.click(function(){
      hearo.elements.savebutton.spin().revert();
    });

    /* Radial progress bar */

    $('.sl-upload-bar')
      .knob({
        width: 27,
        fgColor: 'rgba(0,0,0,0.45)',
        displayInput: true,
        bgColor: 'transparent',
        thickness: 0.2,
        readOnly: true });

    $i_agree.click(submit_artist_agreement);

    $agreed.change(update_i_agree_button_state);

    $.each([$line1, $line2, $city, $state, $zip], function(){
      this.typeaction(update_i_agree_button_state);
    });

    $('.error').remove();
    $('.music_upload_input').each(function(){
      bind_upload_button_handler($(this));
    });

    /* Song listing changes */

    $('#legal_container input').each(function() {
      $(this).typeaction(changePrivateLocation);
    });

    $("#add_country").localsuggest(hearo.geography.countries, {
      floating: true,
      callback: function(value){
        if (value == ""){
          $('[usonly]').hide();
          $('#add_city').removeClass('siamese');
          $("#international-disclaimer").hide();
        } else if (value == "United States"){
          $('[usonly]').show();
          $('#add_city').addClass('siamese');
          $("#international-disclaimer").hide();
        } else {
          $('[usonly]').hide();
          $('#add_city').removeClass('siamese');
          $("#international-disclaimer").show();
        }
      }});


    setTimeout(function(){
      $('.song.listing:not(.pending)').each(function(){
        bind_song_listing_events($(this));
      });
      $('.album.listing').each(function(){
        bind_album_listing_events($(this));
      });
    }, 500);

   /*
    * Other setup
    */

    $('#nonalbum').filedrop({
      dragOver: function(){
        //console.log("OVER");
      },
      drop: function(){
        //console.log("DROP");
      }
    })
    $('button#new-album').click(create_new_album);

   /*
    * $document.ready exports
    */

  };

 /*
  * global exports
  */

  hearo.setup.dashboard.music = setup;

}());
