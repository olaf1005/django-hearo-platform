



(function(){

  var setup = function(){

  hearo.elements.savebutton.show();

  var save_timeout, arm_save = function(){
    clearTimeout(save_timeout);
    save_timeout = setTimeout(save, 1000);
  };

  var $acct_holder = $("#bank-acct-holder"),
      $acct_number = $("#bank-acct-number"),
      $routing_number = $("#bank-routing-number");

  $acct_number.whitelist("0123456789");
  $routing_number.whitelist("0123456789");

  function check_bank_account_info(){
    return ($acct_holder.val().length < 5) ? false :
           ($acct_number.val().length < 8) ? false :
           ($acct_number.val().match(/[^0-9]/) != null) ? false :
           ($routing_number.val().length < 6) ? false :
           ($routing_number.val().match(/[^0-9]/) != null) ? false : true;
  }

  function update_cash_out_button_state(){
    var $cb = $("#green-cash-out-button");

    if (check_bank_account_info()){
      $cb.removeClass('disabled');
      $cb.parent().removeClass('disabled');
    } else {
      $cb.parent().addClass('disabled');
    }
  }

  function save(){
    /* POST data from profile view to endpoint */
    update_cash_out_button_state();

    if (check_bank_account_info()){

      hearo.elements.savebutton.spin();
      $.ajax({
        type: "POST",
        url: "/payment/update_bank_info",
        dataType: "json",
        data: {
          name: $acct_holder.val(),
          account_number: $acct_number.val(),
          routing_number: $routing_number.val(),
          csrfmiddlewaretoken: csrfTOKEN
        },
        success: function(data) {
          //console.log(data);
          hearo.elements.savebutton.revert();
        }
      });
    }
  }

  function disable_cashout_section_for_request(){
    $("#cash-out-button-container").addClass("disabled");
    $("#my-balance").animate({ opacity: "0.5" }, 500);
  }


  function reload_content_after_successful_cashout(){
    hearo.utils.refreshSection("*", function(){
      $("#cash-out").hide();
      $("#tryna-make-that-dolla").show();
    });
  }

  $("#green-cash-out-button").click(function() {
    var $self = $(this);
    if ($self.hasClass("disabled")) return;
    $self.button_spin();
    disable_cashout_section_for_request();

    $.ajax({
      type: "POST",
      url: "/payment/cash_out",
      data: { csrfmiddlewaretoken: csrfTOKEN },
      dataType: "json",
      success: function(data){
        reload_content_after_successful_cashout();
      }
    });
  });

  $("#bank-info input").typeaction(arm_save);
  update_cash_out_button_state();


  }

  $("button#save").click(function(){
    hearo.elements.savebutton.spin().revert();

  });

  hearo.setup.dashboard.payment = setup;

}());
