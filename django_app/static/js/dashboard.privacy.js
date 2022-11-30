 /*global
  hearo,
  */

(function(){
  var setup = function(){

  hearo.elements.savebutton.show();

   /*
    * Helper methods
    */
    var request;
    var updatePassword = function(){
    }
    var save = function(){
      /* POST data from profile view to endpoint */
      hearo.elements.savebutton.spin();

      if(request){
        request.abort();
      }
      var request = $.ajax({
        type: 'POST',
        url: '/my-account/user-settings-ajax/',
        dataType: 'json',
        data: {
          'csrfmiddlewaretoken': csrfTOKEN,
          'email' : $("#id_em").val(),
          'name' : $("#id_name").val(),
        //   'directory_privacy': $('#directory_opt').attr('value'),
        //   'music_privacy': $('#music_opt').attr('value'),
        //   'shows_privacy': $('#shows_opt').attr('value'),
          'fanmail_privacy': $('#fanmail_opt').attr('value'),
        //   'downloads_privacy': $('#downloads_opt').attr('value'),
          'profile_privacy': $('#profile_opt').attr('value'),

          'receive_weekly_digest': getChecked($('#receive_weekly_digest')),
          'receive_monthly_digest': getChecked($('#receive_monthly_digest')),
          'notify_fan_mail': getChecked($('#notify_fan_mail')),
          'notify_review': getChecked($('#notify_review')),
        //   'notify_tip': getChecked($('#notify_tip')),
        //   'notify_downloads': getChecked($('#notify_downloads')),
          'notify_fan': getChecked($('#notify_fan')),
          'notify_fan_threshold': $('#notify_fan_threshold').val(),
          'notify_play': getChecked($('#notify_play')),
          'notify_play_threshold': $('#notify_play_threshold').val(),
        //   'notify_events': getChecked($('#notify_events')),
          },
          success: function(data){
              var error, changed, parsed  = data;
              error = parsed[0];
              changed = parsed[1];
              //console.log(error);
              if(error.length > 0){
                for(ei in error){
                  var e = error[ei];
                  if(e == 'email_in_use'){
                    flashError("Email already in use!");
                  }else if(e == 'password_mismatch'){
                    flashError("Passwords do not match!");
                  }else if(e == 'invalid_current_password'){
                    flashError("Invalid current password");
                  }
                }
              }
              if(changed === 't'){
                  $("#regular_pass").show();
                  $("#reset_pass").hide();
                  document.location = "/join/";
              }
              $("input[type=password]").val('');
          },
          complete: hearo.elements.savebutton.revert
      });
    }
    var save_timeout, arm_save = function(){
      /* Delay save, reset if another change occurs. */
      clearTimeout(save_timeout);
      save_timeout = setTimeout(save, 1000);
    };

    $('button#deactivate-account').click(function(){
      var deactivate = confirm('Are you sure you wish to deactivate your account? This is an irreversible action.');
      if (deactivate == true){
        document.location='/deactivate-account/';
      }
    });


   /*
    * Bind event handlers
    */

    $('button#save').click(save);
    $(document).on('blur','#content.privacy input:text', arm_save);
    $(document).on('change','#content.privacy input:checkbox',arm_save);
    $(document).on('blur','#content #id_pass2',function(e){
        if ($(this).val() != ''){
            $('html, body').animate({scrollTop:0}, 'slow'); /*Scroll up to show any error messages on password save */
            arm_save();
        }
    })

    $('button#change-password').on('click', function(){
      // start spinner
      var self = $(this);
      $(this).addClass('spinning').addClass('disabled');
      var request = $.ajax({
        type: 'POST',
        url: '/my-account/change-password-ajax/',
        dataType: 'json',
        data: {
          'csrfmiddlewaretoken': csrfTOKEN,
          'email' : $("#id_em").val(),
          'curpass' : $("#id_curpass").val(),
          'pass' : $("#id_pass").val(),
          'pass2' : $("#id_pass2").val(),
          },
          success: function(data){
            self.removeClass('spinning').removeClass('disabled');
            $('html, body').animate({scrollTop:0}, 'slow');
            var error, changed, parsed  = data;
            error = parsed[0];
            changed = parsed[1];
            if(error.length > 0){
                for(ei in error){
                    var e = error[ei];
                    if(e == 'email_in_use'){
                        flashError("Email already in use!");
                    }else if(e == 'password_mismatch'){
                        flashError("Passwords do not match!");
                    }else if(e == 'invalid_current_password'){
                        flashError("Invalid current password");
                    }
                }
            }
            if(changed){
                document.location = "/join/";
            }
        }
        , error: function(data) {
          self.removeClass('spinning').removeClass('disabled');
          flashError(data.responseText);
        }
    });
});

   /*
    * Other setup
    */
    $("#deactivate-account, #deactivate-account button").attr("tabindex", "-1"); /*prevent focus on remove profile button */


   /*
    * $document.ready exports
    */
    window.hearo.elements.savebutton.func = save;

  };

 /*
  * global exports
  */
  window.hearo.setup.dashboard.privacy = setup;

//  hearo.setup.node = setup;

}());
