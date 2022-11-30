$(function(){
	//set progress bar
	if($('#progress').length){
		var progress = $('#progress').val();
		$('#register-progress li').each(function(){
			if($(this).index() < progress){
				$(this).addClass('completed');
			}
		})
	}

	/*
    * Screen 1 - Signup
    */

    $('#acctype-sel li a').click(function(){
      console.info('starting...');
      $('#acctype-sel li a').removeClass('active');
      var type = $(this).attr('id');
      $(this).addClass('active');
      console.info('click=', type);
      change_account_type(type);
      setTimeout(setup_suggestions, 3000);
      setTimeout(update_inputs, 3000);
    });




	//submit form
    $('#initial-signup').on('click',function(){
      var self = $(this);
      var account_type = $('#acctype-sel li a.active').attr('id')
      $(this).addClass('spinning').addClass('disabled');

      if (!$('#accept').is(':checked')){
        $(this).removeClass('spinning').removeClass('disabled');
        return flashError('You need to agree to the terms!');
      }

      if (account_type == ""){
        $(this).removeClass('spinning').removeClass('disabled');
        return flashError('You need to select an account type.');
      }

      if ($("#password").val().length < 6){
        $(this).removeClass('spinning').removeClass('disabled');
        return flashError('Password must be at least 6 characters.');
      }

      var is_musician = ($('#id_is_musician').val() == 'on' ? 1 : 0);

      $.ajax({
        type: 'POST'
        , url: '/register-ajax/'
        , data: {
          'csrfmiddlewaretoken': csrfTOKEN,
          'account_type' : account_type,
          'name' : $('#id_name').val(),
          'email' : $('#email').val(),
          'password' : $('#password').val(),
          'city' : $('#id_city').val(),
          'genre' : $('#id_genres').val(),
          'instruments' : $('#id_instruments').val(),
          'write_music' : getChecked($('#id_write_music')),
          'dj' : getChecked($('#id_dj')),
          'teacher' : getChecked($('#id_teacher')),
          'producer' :getChecked($('#id_producer')),
          'engineer' : getChecked($('#id_engineer')),
          'join_band' : getChecked($('#id_join_band')),
          'is_musician' : is_musician
        }
        , success: function (data) {
          self.removeClass('spinning').removeClass('disabled');
          ajaxGo(data);
          $.get("/refresh-header/", function(html){
            $("#header-bar").html(html);
            setupListeners();
          });
        }
        , error: function(data) {
          self.removeClass('spinning').removeClass('disabled');
          flashError(data.responseText);
        }
      });

    })

    function flashError(msg) {
      $('.error').show().text(msg);
    }

    var update_inputs = function(){
      // ensure that all inputs have the same content
      /* Text */
      $('[name="biography"]').val($('[name="biography"]:visible').val());
      $('[name="influences"]').val($('[name="influences"]:visible').val());
      $('[name="experience"]').val($('[name="experience"]:visible').val());
      $('[name="goals"]').val($('[name="goals"]:visible').val());
      $('[name="genres"]').val($('[name="genres"]:visible').val());
      $('[name="instruments"]').val($('[name="instruments"]:visible').val());
      $('[name="city"]').val($('[name="city"]:visible').val());

      /* Musician questions */
      $('[name="start_band"]').val($('[name="start_band"]:visible').val());
      $('[name="join_band"]').val($('[name="join_band"]:visible').val());
      $('[name="write_music"]').val($('[name="write_music"]:visible').val());
      $('[name="teacher"]').val($('[name="teacher"]:visible').val());
      $('[name="is_musician"]').val($('[name="is_musician"]:visible').val());
      $('[name="producer"]').val($('[name="producer"]:visible').val());
      $('[name="dj"]').val($('[name="dj"]:visible').val());
      $('[name="engineer"]').val($('[name="engineer"]:visible').val());
      $('[name="new_people"]').val($('[name="new_people"]:visible'));
    };

    /*
     * Screen 1 - Social connect
     */
    //init inviete
    hearo.utils.invite.init();
    //open share window
    $('#onboarding .social-connect').on('click',function(e){
        e.preventDefault();
        window.open(this.href,'targetWindow',
            'toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes,width=600,height=400');
        });
})
