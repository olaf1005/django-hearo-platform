(function(){
  var setup = function(){

    hearo.elements.savebutton.show();

    /*
     * Helper methods
     */
    var request;
    var save = function(){
      /* POST data from profile view to endpoint */
      hearo.elements.savebutton.spin();
      if(request){
        request.abort();
      }
      var request = $.ajax({
        type: 'POST',
        url: '/my-account/account-profile-ajax/',
        data: {
          csrfmiddlewaretoken: csrfTOKEN,
          /* Account type */
          account_type: $('#acctype-sel li a.active').attr('id'),

          /* Text */
          biography :   $('[name="biography"]:visible').val(),
          influences :  $('[name="influences"]:visible').val(),
          experience :  $('[name="experience"]:visible').val(),
          goals :       $('[name="goals"]:visible').val(),
          genre :       $('[name="genres"]:visible').val(),
          instruments : $('[name="instruments"]:visible').val(),
          city :        $('[name="city"]:visible').val(),

          /* Musician questions */
          start_band :  getChecked($('#id_start_band')),
          join_band :   getChecked($('#id_join_band')),
          write_music : getChecked($('#id_write_music')),
          teacher :     getChecked($('#id_teacher')),
          is_musician : getChecked($('#id_is_musician')),
          producer :    getChecked($('#id_producer')),
          dj :          getChecked($('#id_dj')),
          engineer :    getChecked($('#id_engineer')),
          new_people :  getChecked($('#id_new_people'))

        },
        success: function(data){
          // pass
	  setTimeout(update_inputs, 3000);
        },
        complete: hearo.elements.savebutton.revert
      });
    };

    var save_timeout, arm_save = function(){
      /* Delay save, reset if another change occurs. */
      clearTimeout(save_timeout);
      save_timeout = setTimeout(save, 1000);
    };

    /*
     * Event handlers
     */

    // change account type
    $('#acctype-sel li a').click(function(){
      //console.info('starting...');
      $('#acctype-sel li a').removeClass('active');
      var type = $(this).attr('id');
      $(this).addClass('active');
      //console.info('click=', type);
      change_account_type(type);
      arm_save();
      setTimeout(setup_suggestions, 3000);
      setTimeout(update_inputs, 3000);
    });


    // buttons for membership administration
    $('button.make-admin').click(make_user_admin);
    $('button.make-member').click(make_user_member);
    $('button.delete').click(remove_user_from_page);
    $('input.percentage_membership_split').change(update_membership_percentage);

    // save button
    $('button#save').click(save);
    // TODO: REBASE CHECK
    //$('#id_city').autosuggest('/my-account/location-ajax/'); /* Setup autosuggest for Where in the world... */
    // TODO: REBASE CHECK Autosaving
    //$('#content .musician_question_text').find('input:checkbox').change(arm_save);
    $(document).on('blur','#content.profile input,#content.profile textarea',
        function (e) {
            if (!$(e.target).is(':checkbox')) {
                arm_save();
            }
        });

    setup_suggestions();
    update_inputs();

   /*
    * Other setup
    */

   /*
    * $document.ready exports
    */

    window.hearo.elements.savebutton.func = save;

  };

 /*
  * global exports
  */
  window.hearo.setup.dashboard.profile = setup;
}());
