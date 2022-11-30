window.APIROOT = '/api/v0/'

hearo.mixins.APICall = function (opts) {

  // .on(event, callback) helper object
  var callbacks = {
    success: function(){}
  , complete: function(){}
  , error: function(response){
    if (response.status == 401){
      loginRequired();
    }
  }
  , on: function(type, callback) {
    switch (type){
      case 'success':
        this.success = callback;
        break;
      case 'complete':
        this.complete = callback;
        break;
      case 'error':
        this.error = callback;
        break;
    }
    return this;
    }
  }

  opts = $.extend({}, {
    type: 'GET'
  }, opts);

  $.ajax({
    type: opts.type
  , url:  APIROOT + opts.url
  , data: opts.data
  , dataType: 'json'
  , success:  function(e){ callbacks.success(e) }
  , complete: function(e){ callbacks.complete(e) }
  , error:    function(e){ callbacks.error(e) }
  });

  return callbacks;

}



