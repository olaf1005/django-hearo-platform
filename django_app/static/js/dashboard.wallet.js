(function () {
    var setup = function () {
        /*
         * Helper methods
         */

        function validate_confirm_send_form() {
            var has_error = false;
            if ($("#id_pass").val() === "") {
                has_error = true;
            }
            return has_error;
        }

        function validate_send_form() {
            var has_error = false;
            var wallet_balance = document.querySelector(
                "#wallet-balance-value"
            );
            var balance = wallet_balance.dataset.balance;

            console.log("Balance is", balance);

            // test if empty
            if ($("#id_to_account").val() === "") {
                $("#id_to_account-container").addClass("input-error");
                has_error = true;
            }

            // TODO: need to verify its a valid hedera address

            // test if empty
            if ($("#id_amount").val() === "") {
                $("#id_amount-container").addClass("input-error");
                has_error = true;
            }

            // test to ensure its a number
            if (isNaN(parseInt($("#id_amount").val()))) {
                $("#id_amount-container").addClass("input-error");
                has_error = true;
            }

            // test to ensure value is less than balance
            if (parseInt($("#id_amount").val()) > parseInt(balance)) {
                $("#id_amount-container").addClass("input-error");
                has_error = true;
            }

            // memo field is only validated for specific exchanges
            var bitrue = "0.0.285576";
            var exchanges_requiring_memo = [bitrue];

            if (
                exchanges_requiring_memo.includes($("#id_to_account").val()) &&
                $("#id_memo").val() === ""
            ) {
                $("#id_memo-container").addClass("input-error");
                has_error = true;
            }

            return has_error;
        }

        function clear_send_form() {
            $(".input-error").removeClass("input-error");
        }

        function toggle_send_form_submit_spin() {
            $("#modal-send-jam-btn").toggleClass("disabled").toggleClass('spinning');
        }

        function toggle_confirm_send_form_submit_spin() {
            $("#modal-send-jam-btn-2").toggleClass("disabled").toggleClass('spinning');
        }

        function show_confirm_send_jam_modal() {
            // show confirmation modal
            let sending_to_account = $('#id_to_account').val();
            $('#id_sending_to').text(sending_to_account);
            let sending_amount = $('#id_amount').val();
            $('#id_sending_amount').text("Ɉ" + sending_amount);
            let sending_with_memo = $('#id_memo').val();
            $('#id_sending_memo').text(sending_with_memo);

            $('#modal-cancel-send').trigger('click');
            $('#send-jam-confirm').trigger('click');
        }

        function send_jam() {

            var request;
            /* POST data from profile view to endpoint */
            if (request) {
                request.abort();
            }

            let sending_to_account = $('#id_to_account').val();
            let sending_amount = $('#id_amount').val();
            let sending_with_memo = $('#id_memo').val();
            let pass = $('#id_pass').val();

            var request = $.ajax({
                type: "POST",
                dataType: "json",
                url: "/my-account/send-jam/",
                data: {
                    csrfmiddlewaretoken: csrfTOKEN,
                    to_account: sending_to_account,
                    amount: sending_amount,
                    memo: sending_with_memo,
                    pass: pass,
                },
                success: function (data) {
                    $("#modal-cancel-send-2").trigger('click');
                    // show confirmation modal

                },
                complete: toggle_confirm_send_form_submit_spin,
            });
        }

        function confirm_send_jam_modal() {

            clear_send_form();

            toggle_confirm_send_form_submit_spin();

            let form_has_errors = validate_confirm_send_form();

            if (form_has_errors) {
                toggle_confirm_send_form_submit_spin();
                return false;
            }

            send_jam();

            toggle_confirm_send_form_submit_spin();

            // validate password and send
            // show_send_confirmed();

        }


        function send_jam_modal() {

            clear_send_form();

            toggle_send_form_submit_spin();

            let form_has_errors = validate_send_form();

            if (form_has_errors) {
                toggle_send_form_submit_spin();
                return false;
            }

            toggle_send_form_submit_spin();

            show_confirm_send_jam_modal();

        }

        /*
         * Event handlers
         */

        hearo.elements.savebutton.hide();

        $("#modal-send-jam-btn").on("click", send_jam_modal);
        $("#modal-send-jam-btn-2").on("click", confirm_send_jam_modal);

        /*
         * Other setup
         */
        modalEffectsInit();

        /*
         * $document.ready exports
         */
    };

    /*
     * global exports
     */
    window.hearo.setup.dashboard.wallet = setup;
})();
