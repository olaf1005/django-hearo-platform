(function(){

  var SplashPage = Backbone.View.extend({
    el: '#content.home'
  , events: {
      'click button#submit-registration': 'processRegistration'
    }

  , processRegistration: function () {
      var self = this;
      this.$('button').addClass('spinning');

      if (!this.$('input:checkbox').is(':checked')){
        this.$('button').removeClass('spinning');
        return this.flashError('You need to agree to the terms!');
      }

      $.ajax({
        type: 'POST'
      , url: '/register-ajax/'
      , data: {
        'csrfmiddlewaretoken': csrfTOKEN,
        'name' : $('#name').val(),
        'email' : $('#email').val(),
        'password' : $('#password').val(),
        'is_musician' : 1
        }
      , success: function (data) {
          document.location = data;
        }
      , error: function(data) {
          self.$('button').removeClass('spinning');
          self.flashError(data.reponseText);
        }
      });
    }

  , flashError: function (msg) {
      self.$('.error').show().text(msg);
      setTimeout(function() {
        self.$('.error').hide()
      }, 5000);

    }

  });

}());
