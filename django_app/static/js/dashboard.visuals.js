 /*global
  hearo,
  */

(function(){
  var setup = function(){

    hearo.elements.savebutton.show();
    /*
    * Helper methods
    */

    var $photos_upload_button = $('#profile_photos #choose_button');
    var request; /*save ajax request */
    var update_banner = function(commit){
      /* By default, we commit to backend on every update. */
      if (commit === undefined) commit = true;

      /* Check font selected */
      var chosen_font = $('#banner_typeface input:checked').attr('value');

      /* Check features selected */
      name =       $('#id_name_bool').is(':checked'),
      instrument = $('#id_instrument_bool').is(':checked'),
      //genre =      $('#id_genre_bool').is(':checked'),
      plocation =   $('#id_location_bool').is(':checked'),
      white_bar =  $('#id_bar_bool').is(':checked');

      use_uploaded = $('#banner_options input:checked').attr('value') === 'uploaded';

      /* Update the previews */
      $('.choice .contents_preview').each(function(){
        var $this = $(this);
        /* Update typeface */
        $this.find('.username').attr('class', 'username ' + chosen_font);
        /* Hide name if not selected */
        name ?
          $this.find('.username').show():
          $this.find('.username').hide();
        /* Hide white bar if not selected */
        white_bar ?
          $this.find('.bar').addClass('white'):
          $this.find('.bar').removeClass('white');
        instrument ?
          $this.find('.userinstrument').show():
          $this.find('.userinstrument').hide();
        /* Hide location if not selected */
        plocation ?
          $this.find('.userlocation').show():
          $this.find('.userlocation').hide();
      });

      /* Saving changes */
      if (commit){

          hearo.elements.savebutton.spin();

          if(request){
            request.abort();
          }
          var request = $.ajax({
            type: 'POST',
            url: '/my-account/banner-ajax/',
            data: {
              font: chosen_font,
              display_title:            name ? 't' : 'f',
              //display_genre:           genre ? 't' : 'f',
              display_instrument: instrument ? 't' : 'f',
              display_location:    plocation ? 't' : 'f',
              display_bar:         white_bar ? 't' : 'f',
              uploading_bool:   use_uploaded ? 't' : 'f'
            },
            dataType: 'json',
            success: function(){
              hearo.elements.savebutton.revert();
            }
          });
      }
    };

    var save_timeout,update_timeout,arm_save = function(){
      /* Delay save, reset if another change occurs. */
      clearTimeout(save_timeout);
      clearTimeout(update_timeout);
      save_timeout = setTimeout(function() {update_banner(false);}, 300);
      update_timeout = setTimeout(function() {update_banner(true);}, 1000);
    };

    var make_photo_container = function(data){
        $photo = $(data.html);
        $photo.find('button.delete').one('click', photo_delete_action);
        $photo_drop_hint.after($photo);
        $photo_drop_hint.hide().find('.spinner').stopspin();
    }

    var upload_photos = function(photos){
      var formData = new FormData();
      formData.append('photo', photos[0]);

      $photo_drop_hint.show().find('.spinner').show().spin();
      $photo_drop_hint.find('span').hide();

      $.ajax({
        url: '/my-account/photos-ajax/',
        type: 'POST',
        data: formData,
        complete: function(xhr){
          var data = JSON.parse(xhr.responseText);
          make_photo_container(data);
          if (photos.length > 1){
            upload_photos(photos.slice(1));
          }
        },
        cache: false,
        contentType: false,
        processData: false
      });
    };

    /* Change the Profile picture ribbon to a photo given its id */
    var move_ribbon = function(photo_id){
      $('#profile_ribbon').appendTo($(photo_id));
    };

    var photo_delete_action = function(e){
      e.stopPropagation();
      var id = parseInt($(e.target).parent().attr('id').match(/\d+/g)[0]);
      $.post('/my-account/delete-photo/', {id : id, csrfmiddlewaretoken: csrfTOKEN}, function(){
        $(e.target).parent().remove();
      });
    };

    var photo_lightbox_action = function(id){
      createPhotoLightbox(id);
    };

   /*
    * Bind event handlers
    */

    /* Banner drag and drop */

    var $banner_drop_hint = $('#bupload_label .drop_hint'),
        $banner_empty = $('#bupload_label .empty_media'),
        $photo_drop_hint = $('#profile_photos .drop_hint');

    $('#banner_settings').filedrop({
      url: '/upload-banner-temp/',
      paramname: 'texture',
      data: {
        csrfmiddlewaretoken: window.csrfTOKEN
      },
      headers: {
        'Cache-Control': 'no-cache'
      },
      allowedfiletypes: ['image/jpeg', 'image/png'],
      maxfiles: 1,
      maxfilesize: 10,
      dragOver: function(){
        $banner_drop_hint.show();
        $banner_empty.hide();
        $photo_drop_hint.hide();
      },
      docLeave: function(){
        $banner_drop_hint.hide();
        $banner_empty.show();
      },
      drop: function(){
        $banner_drop_hint.find('span').hide();
        $banner_drop_hint.find('.spinner').show().spin();
      },
      uploadFinished: function(i, file, response, time){
        window.createBannerUploadLightbox();
        $banner_drop_hint.fadeOut().find('.spinner').stopspin().remove();
        setTimeout(function(){
          $banner_drop_hint.find('span').show();
        }, 10);
      }
    });

    /* Photo drag and drop */

    var photos_done = false;

    $('#profile_photos').filedrop({
      url: '/my-account/photos-ajax/',
      paramname: 'photo',
      data: {
        csrfmiddlewaretoken: window.csrfTOKEN
      },
      headers: {
        'Cache-Control': 'no-cache'
      },
      allowedfiletypes: ['image/jpeg', 'image/png'],
      maxfiles: 10,
      maxfilesize: 10,
      dragOver: function(){
        $photo_drop_hint.show();
        $banner_drop_hint.hide();
        $banner_empty.show();
      },
      drop: function(){
        photos_done = false;
        $photo_drop_hint.find('span').hide();
        $photo_drop_hint.find('.spinner').show().spin();
      },
      uploadFinished: function(i, file, response, time){
        make_photo_container(response);
      },
      afterAll: function(){
        photos_done = true;
        $photo_drop_hint.hide().find('.spinner').stopspin();
        $photo_drop_hint.find('span').show();
      }
    });

    $('button.delete').one('click', photo_delete_action);

    $('.photo_container').on('click', function(){
      photo_lightbox_action(parseInt(this.id.match(/\d+/g)[0]));
    });
    /*
     * Some bug with document.ready is messing up how this gets bound
     * unless we use a short timeout.
     */
    setTimeout(function(){
      $('#photo_input').change(function(){
        var files = [];
        $.each(this.files, function(i, file){
          files.push(file);
        });
        upload_photos(files);
        /* Reset it */
        this.value = '';
       });
    }, 10);

    $('#banner_display input:checkbox, #banner_typeface input:radio, #banner_options input:radio').change(arm_save);

   /*
    * Other setup
    */



   /*
    * $document.ready exports
    */

  };

 /*
  * global exports
  */

  window.hearo.setup.dashboard.visuals = setup;

}());
