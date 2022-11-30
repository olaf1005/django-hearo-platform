/*global $, player, Stripe, createElem */

(function() {

    $('#card_number').keypress(function(e){
        // Don't accept non-digits
        if (e.which > 57 || e.which < 48){
            return false;
        }
        if ($(this).val().length % 4 === 0){
            $(this).val($(this).val() + ' ');
        }
    });

    function creditCardFeedback(msg){
      $("#payment-errors").show().html(msg);
    }

    function stripeResponseHandler(status, response) {
        var token, card, last4, cardType, card_table, new_card;
        if (response.error) {
            //show the errors on the form
            creditCardFeedback(response.error.message);

        } else {
              // token contains id, last4, and card type
              token = response.id;
              card = response.card;
              last4 = card.last4;
              cardType = card.type;
              $('#card_number').val('');
              $('#card_mm').val('MM').addClass('grey');
              $('#card_yyyy').val('YYYY').addClass('grey');
              $('#card_cvc').val('');

            $.ajax(
          "/payment/add_card",
          {
              dataType: "json",
              type: "post",
              data: {'token': token,
               'last4': last4,
               'cardType': cardType},
              success: function(data) {
            creditCardFeedback(data.message);
            if (data.success) {
                new_card = $('<div class="credit_card" id="card_' + data.card_pk + '"><div class="card_number">■■■■ ■■■■ ■■■■ ' + last4 + '</div><div class="card_type ' + cardType + '"></div><div class="delete_button" onclick="removeCard(' + data.card_pk + ');"></div></div>');
                $('#add_card').before(new_card);
                player.syncCreditCards();
            }
              }
          });
        }
    }

    function setupStripe() {
	$(".card_delete").live('click', function(e) {
	    var url;
	    e.preventDefault();

	    $(this).off('click'); // disable the weird event handlers from myaccounts

	    url = $(this).attr("href");
	    $(this).parent().parent().remove();
	    $.get(url, null, function(data) {
		if ($.parseJSON(data).none) {
		    $('#cards').addClass('hidden');
		    $('#no_cards_message').removeClass('hidden');
		}
		player.syncCreditCards();
		player.syncDownloadQueueInterface();
	    });
	});

	$("#card-submit").click(function(event) {
      // disable the submit button to prevent repeated clicks
            $('#payment-errors').hide();
      if ($('#card_number').val() === '' || $('#card_cvc').val() === '' || $('#card_mm').val() === '' || $('#card_yyyy').val() === '') {
          creditCardFeedback('Fill in all fields');
          return false;
      }
      $('#card-submit').attr("disabled", "disabled");
      creditCardFeedback('Processing...');

      Stripe.createToken({
          number: $('#card_number').val(),
          cvc: $('#card_cvc').val(),
          exp_month: $('#card_mm').val(),
          exp_year: $('#card_yyyy').val()
      }, stripeResponseHandler);

      // prevent the form from submitting with the default action
      return false;
	});

    }

    //export
    window.setupStripe = setupStripe;

}());
