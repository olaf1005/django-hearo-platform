hearo.utils.invite = {
	init: function () {
		//send band invites
		$('#submit_band_invite').on('click',function(){
			$.ajax({
				url  : '/send-invites/',
				type : 'POST',
				data : {
					'emails' : $('#band_invites').val(),
					'csrfmiddlewaretoken' : csrfTOKEN,
				},
				success : function(response){
					if (response == 'invites sent') {
						$('#band_invites').val('');
						hearo.utils.invite.flash('#band_invites_sent');
					}
					else {
						hearo.utils.invite.flash('#band_invites_error');
					}
				}
			});
		})
	},
	flash: function(selector) {
		$(selector).css('display', 'inline-block');
		setTimeout(function(){
			$(selector).fadeOut(1500);
		}, 2000);
	}
}