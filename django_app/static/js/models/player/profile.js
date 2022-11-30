
window.Profile = hearo.Model.extend({

  initialize: function () {
    var self = this;

    // Support for adding preloaded attributes
    if (this.get('preloaded')){
     if (window.DEVELOPER !== undefined) {
        self.set('path', "http://5d9cc604aa46212441a1-8d91fd2e4df7768dcceba1b31a06f709.r5.cf1.rackcdn.com/B2_fad2473f209446a08854088b703d7f65.mp3");
      }
      return;
    }


    // Get the song info from the API endpoint
    this.fetch({ async: !$.browser.is_mobile, success: function () {
	self.trigger('ready');
    }});
  }


, url: function () {
    return APIROOT + 'profile~' + this.get('id');
  }

, parse: function(response) {
  /*
   * response returns:
  dtj: false
  fand: false
  account_type: "band"
  id: 3715
  img_path: ""
  keyword: ""
  name: ""
  onair: false
  short_name: ""
  sqr_path: ""
  url: ""*
  */
    return {
      id      : response.id
    , type    : 'profile'
    //, fanned  : response.fand
    , artwork : response.sqr_path
    , artistName: response.name
    , artistKeyword: response.keyword
    , priceVal: 0.99
    }
  }

, tip: function () {
    var self = this;
    $("#open-download-queue").addClass('.spinning');
    return this.APICall({
      type: 'POST'
    , url:  'queues/downloads'
    , data: {
        id: self.get('id')
      , type: 'profile'
      }
    }).on('success', function () {
      hearo.player.downloads.collection.fetch();
      $("#open-download-queue").removeClass('.spinning');
    }).on('error', function(response){
      if (response.status == 401){
        loginRequired();
      }
    });
  }

});


