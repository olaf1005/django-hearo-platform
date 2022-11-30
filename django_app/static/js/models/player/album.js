window.Album = hearo.Model.extend({

  initialize: function () {
    var self = this;

    this.fetch({ async: !$.browser.is_mobile,  success: function () {
      self.trigger('ready');
    }});

  }

, url: function () {
    return APIROOT + 'album~' + this.get('id');
  }

, parse: function (response) {
  var first = true;
  var songs = response.songs.map(function (song) {
    var attrs = Song.prototype.parse(song);
    if ($.browser.is_mobile){
      if (first){
	first = false;
      } else {
	attrs.preloaded = true;
      }
      return new Song(attrs);
    } else {
      // Don't do an AJAX call - we already have its info
      attrs.preloaded = true;
      return new Song(attrs);
    }
  });

  first = true;
  _.forEach(songs, function (song)  {
    if ($.browser.is_mobile){
      if (first){
	first = false;
      } else {
       hearo.player.queueSong(new QueuedSong(song.attributes));
      }
    }
     });

    return {
      id       : response.id
    , is_nyp   : response.download_type === 'name_price' ? true : false
    , owned    : response.owned
    , artist   : response.artist
    , type     : 'album'
    , title    : response.title
    , songs    : songs
    , price    : response.price
    , priceVal : response.priceVal
    , released : response.year_released
    , cover    : {
        small:  response.small_cover
      , medium: response.small_medium
      , full:   response.small_full
      }
    }

  }

, download: function () {
    // TODO refactor this with Song.download
    var self = this;
    $("#open-download-queue").addClass('spinning');
    return this.APICall({
      type: 'POST'
    , url:  'queues/downloads'
    , data: {
        id: self.get('id')
      , type: 'album'
      }
    }).on('success', function () {
      hearo.player.downloads.collection.fetch();
      $("#open-download-queue").removeClass('spinning');
    }).on('error', function(response){
      if (response.status == 401){
        loginRequired();
      }
    });

  }

});
