/* registrationForm.js

 */

//import
/*global
console,
createElem,
csrfTOKEN : false,
 */

(function(){
    function error(message){
        var er =$(createElem('span',{className : "error"}, message));
        return er;
    }
    function okay(message){
        var er =$(createElem('span',{className : "success"}, message));
        return er;
    }
    function checkPassword(){
        $("#pass .response").empty();
        if ($("#id_pass").val().length < 6){
            $("#pass .response").append(error("Need at least 6 character password"));
            return false;
        }
        else if($("#id_pass").val() == "password"){
            $("#pass .response").append(error("Invalid password"));
            return false;
        }
        else{
            $("#pass .response").append(okay("Nice password ;)"));
            return true;
        }
    }
    function checkName(){
        $("#name .response").empty();
        var last,first = $("#id_first_name").val();
        last = $("#id_last_name").val();
        if(first === "first name"){first = "";}
        if(last === "last name"){last = "";}
        if(first === "" || last === ""){
            $("#name .response").html(error("You need a first/last name!"));
            return false;
        }
        else{
            $("#name .response").html(okay("Hey "+first+"!"));
            return true;
        }
    }
    function checkEmail(){
        var good = false;
        $("#email .response").empty();
        $.ajax({
            type : "GET", url : "/check-register-email/",
            data : {'email':$("#id_reg_email").val()},
            success : function(data){
                if(data === ""){
                    $("#email .response").html(okay("We'll send you a verification email!"));
                    good = true;
                }
                else{
                    $("#email .response").html(error(data));
                }
            },
            async:false
        });
        return good;
    }
    function checkPasswordAgain(){
        $("#pass_again .response").empty();
        var first, again;
        first = $("#id_pass").val();
        again = $("#id_pass_again").val();
        if(first === again){
            if (first === "password"){
                $("#pass_again .response").html(error("Invalid password"));
                return false;
            }
            $("#pass_again .response").html(okay("Passwords match"));
            return true;
        }
        else{
            $("#pass_again .response").html(error("Passwords don't match!"));
            return false;
        }
    }
    function checkAccepted(){
        $("#accept .response").empty();
        accepted = $('#id_accept').attr('checked') ? 1 : 0;
        if(accepted === 0){
            $("#accept .response").html(error("You need to agree!"));
            return false;
        }
        return true;
    }
    function checkCorrectRegisterForm(){
        var n,e,p,pa,a;
        n = checkName();
        e = checkEmail();
        p = checkPassword();
        pa = checkPasswordAgain();
        a = checkAccepted();
        console.log(e);
        return n && e && p && pa && a;
    }
    function initRegistrationForm(){
        $("#id_last_name").focusout(function(){checkName();});
        $("#id_reg_email").focusout(function(){checkEmail();});
        $("#id_pass").focusout(function(){checkPassword();});
        $("#id_pass_again").focusout(function(){checkPasswordAgain();});

        $("#id_pass").focus(function(){
            $("#pass .response").append(createElem("span",{},"Password"));
            $("#id_pass").unbind('focus');
        });
        $("#id_pass_again").focus(function(){
            $("#pass_again .response").append(createElem("span",{},"Confirm password"));
            $("#id_pass_again").unbind('focus');
        });
        $("#musician_check").earl({ fontSize: '26px' });
    }

    function registerAjax(){
    var first = $('#id_first_name').val(),
        last = $('#id_last_name').val(),
        email = $('#id_reg_email').val(),
        pass = $('#id_pass').val(),
        passagain = $('#id_pass_again').val(),
        accepted = $('#id_accept').attr('checked') ? 1 : 0;
        is_musician = $("#musician_check").attr("value") === "Musician" ? 1 : 0;
    if(checkCorrectRegisterForm()){
        $.ajax({
                type: 'POST',
                url: '/register-ajax/',
                data: {
                    'csrfmiddlewaretoken': csrfTOKEN,
                    'first_name' : first,
                    'last_name' : last,
                    'email' : email,
                    'password' : pass,
                    'password_again' : passagain,
                    'is_musician' : is_musician
                },
                success: function(data){
                    document.location = data;
                },
                error: function(data){
                    $(".errorMessage").show();
                    $(".errorMessage").text(data.responseText);
                }
            });
    }
}

    //export
    window.initRegistrationForm = initRegistrationForm;
    window.registerAjax = registerAjax;
    window.checkCorrectRegisterForm = checkCorrectRegisterForm;

}());
