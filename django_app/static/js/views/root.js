var Root = hearo.View.extend({
  // Jank Legacy Support during transition to Backbone

  el: 'body'

, events: {
    // LEGACY SUPPORT
    // TODO MOVE THIS OVER TO A BETTER SYSTEM
    'click .playAlbum'  : '_playAlbum'
  //, 'click #download-current': '_downloadSong'
  , 'click [fan_button]'     : '_fan'

  , 'click button[action="play"]'     : 'play'
  , 'click button[action="fan"]'      : '_fan'
  , 'click button[action="review"]'   : '_review'
  , 'click button[action="download"]' : '_download'
  , 'click button[action="tip"]' : '_tip'
  }

, play: function (e) {
    var $bttn = $(e.target)
      , type  = $bttn.attr('play-type')
      , id    = $bttn.attr('play-id');

    if (type === 'song') {
      this._playSong(id, $bttn);
    } else if (type === 'album') {
      this._playAlbum(id, $bttn);
    }

    if (!$.browser.is_mobile){
      // mobile blocks on play so this isn't useful
      $bttn.addClass('spinning');
    }
  }

, _playSong: function (id, $bttn) {
    var song = new QueuedSong({ id: id });

    song.on('ready', function () {
      hearo.player.queueSong(this);
      $bttn.removeClass('spinning');
    });
  }

, _playAlbum: function (id, $bttn) {
    var album = new Album({ id: id });

    album.on('ready', function () {
      _.forEachAsync(this.get('songs'), function (song)  {
	hearo.player.queueSong(new QueuedSong(song.attributes));
      }, 100);
      $bttn.removeClass('spinning');
    });
  }

, _download: function (e) {
    var $button = $(e.target).closest('[elem-id]')
      , id = parseInt($button.attr('elem-id'), 10)
      , type = $button.attr('elem-type');

    if (type === 'song') {
      var song = new SongDownload({ id: id });

      song.on('ready', function () {
        hearo.player.addSongToDownloads(this);
      });
    } else {
      var album = new AlbumDownload({ id: id });

      album.on('ready', function () {
        hearo.player.addAlbumToDownloads(this);
      });
    }
  }
, _tip: function (e) {
    var $button = $(e.target).closest('[elem-id]')
      , id = parseInt($button.attr('elem-id'), 10)
      , type = $button.attr('elem-type');

      var tip = new ProfileTip({ id: id });

      tip.on('ready', function () {
        hearo.player.addProfileTipToDownloads(this);
      });
  }

, _review: function (e) {
    // type id title
    var $button = $(e.target)
      , id = parseInt($button.attr('elem-id'), 10)
      , type = $button.attr('elem-type')
      , title = $button.attr('elem-title')
      , profile = '/profile/' + $button.attr('profile') + '/reviews/';

    if(!$('#reviews').length){
      ajaxGo(profile);
    }

    hearo.setup.reviews.open(type, id, title);
  }

, _fan: function (e) {
    // jank for now
    var $target = $(e.target)
      , unfanning = ($target.attr('fanned') == 'true');

    if (unfanning) {
      window.unfan_this($target.attr('elem-type'), $target.attr('elem-id'), function () {
        setTimeout(function () {
          hearo.player._setTrackerCalc();
        }, 10);
        $target.attr('fanned', 'false');
      })
    } else {
      window.fan_this($target.attr('elem-type'), $target.attr('elem-id'), function () {
        setTimeout(function () {
          hearo.player._setTrackerCalc();
        }, 10);
        $target.attr('fanned', 'true');
      })
    }
  }

, _clickParent: function (e) {
    $(e.target).parent().click();
  }

});

$(document).ready(function () {
  new Root();
});
