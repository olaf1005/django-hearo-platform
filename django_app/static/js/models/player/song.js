/*

  chedda = new Song({
    artist: new Profile({...})
  , id: 2134
  , path: "http://5d9cc604aa46212441a1-8d91fd2e4df7768dcce..."
  , title: "Chedda"
  , price: 0.69
  , fanned: true
  , available: true
  , reviewsCount: 0
  })

*/

window.Song = hearo.Model.extend({

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
    this.fetch({
        async: !$.browser.is_mobile,
        success: function() {
            // testing
            if (window.DEVELOPER !== undefined) {
                self.set(
                    "path",
                    "http://5d9cc604aa46212441a1-8d91fd2e4df7768dcceba1b31a06f709.r5.cf1.rackcdn.com/B2_fad2473f209446a08854088b703d7f65.mp3"
                );
            }
            if ($.browser.is_mobile) {
                // this plays the song on play
                hearo.player.queueSong(self);
            } else {
                self.trigger("ready");
            }
        }
    });
  }


, url: function () {
    return APIROOT + 'song~' + this.get('id');
  }

, parse: function(response) {
    var res = {
      id      : response.id
    , is_nyp  : response.download_type === 'name_price' ? true : false
    , owned   : response.owned
    , type    : 'song'
    , title   : response.title
    , fanned  : response.fanned
    , price   : response.price
    , priceVal: response.priceVal
    , path    : response.path
    , artwork : response.artwork
    , artistName: response.artistName
    , artistKeyword: response.artistKeyword
    }
    // console.info('-->', res);
    return res;
  }

, play: function () {
    // Add the song to the playlist or start playing if it the playlist is empty
    this._initializeSound();
    this._play();
    console.info('play start');
    hearo.player.current = this;
  }

, download: function () {
    var self = this;
    $("#open-download-queue").addClass('.spinning');
    return this.APICall({
      type: 'POST'
    , url:  'queues/downloads'
    , data: {
        id: self.get('id')
      , type: 'song'
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

, fan: function (unfan) {
    // TODO fix this weird arg
    // s.fan().on('success', function(){...}).on('error', function(){ ... });

    return $.ajax({
      type: 'POST'
      // TODO change when fanning api goes up
    , url: '/music/fan-ajax/'
    , data: {
        csrfmiddlewaretoken: csrfTOKEN
      , unfan:  unfan ? 't' : 'f'
      , target: 'song'
      , id:     this.get('id')
      }
    });
  }

, unfan: function () {
    this.fan(true);
  }

, review: function () {
    toggleReviews('song', this.get('id'), this.get('title'));
  }

, _play: function () {
  }

, _loaded: false

, _initializeSound: function () {
    // soundManager setup
    var self = this
      , existing = soundManager.getSoundById(this.get('id'));

    if (existing !== undefined) {
      // This song has been buffered already,
      // so just re-use that sound object.
      this._sound = existing;
      soundManager.setPosition(existing.id, 0);
    } else  {
      // Load the track
      this._createSound();
    }

    this._play = function () {
      if (!self._sound) {
	if ($.browser.is_mobile){
	  return hearo.player.soundManagerNotOk();
	}else{
	  return hearo.player.trigger('soundManagerNotOk');
	}
      }
      self._sound.play({
        onplay: function () {
          this.setVolume(hearo.player.volume);
          // UI change when song is playing
        }
      , onpause: function () {
          // UI change when song isn't playing
        }
      , whileplaying: function () {
          hearo.player.trigger('progress', this.position, this.durationEstimate);
        }
      , onfinish: function () {
          // after song play done
	    hearo.player.skipForward();
          self._loaded = true;
        }
      });
    }
  }

, _createSound: function () {
    var self = this;

    this._sound = soundManager.createSound({
      id: this.get('id')
    , url: this.get('path')
    , stream: true
    , autoLoad: true
    , multiShot: false
    , autoPlay: false
    , whileloading: function () {
        self._loaded = false;
        var percentage = (this.bytesLoaded / this.bytesTotal) * 100;
        hearo.player.trigger('songload', percentage);
    }
    , onload: function () {
      if ($.browser.is_mobile){
	hearo.player._setUIForLoaded();
      }else{
	hearo.player.trigger('songloaded');
      }
    }
      , onfinish: function () {
          // after song play done
	if ($.browser.is_mobile){
	  hearo.player.skipForward();
	  hearo.player._setUIForPlayback();
	  self._loaded = true;
	}
        }
    });
}

});


