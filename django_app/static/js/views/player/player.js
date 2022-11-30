// Rewrite of player

var MusicPlayer = hearo.View.extend({
  initialize: function () {
    var self = this;

    this.els();
    this._initializeTracker();
    this._initializeVolume();
    this._initializeLoader();
    this._resetTimer();

    soundManager.setup({

      preferFlash: false

    , onready: (function () {
        this._initializePlaylist();
        this._initializeDownloads();
        this._setUIForIdle();
        this.setVolume(80);
        this.on('soundManagerNotOk', this._soundManagerFlashWarning);
        this.on('songload', this._setLoader);
        this.on('songloaded', this._setUIForLoaded);
      }).bind(this)
    });

  }

, events: {
    // Playback
    'click button#back'       : 'skipBack'
  , 'click button#forward'    : 'skipForward'
  , 'click button#play-pause' : 'playPause'
  , 'click button#volume-icon' : 'toggleVolume'

    // Queues
  , 'click #open-play-queue'     : 'togglePlaylist'
  , 'click #open-download-queue' : 'toggleDownloads'
  }

, el: '#music-player'

, els: function () {
    this.$playlistCounter = this.$('#open-play-queue').find('.counter').first();
    this.$downloadsCounter = this.$('#open-download-queue').find('.counter').first();
  }

  // We never autoplay so we can assume this
, paused: true

, idle: true

, togglePlaylist: function () {
    $('#playlist').toggleClass('open');
  }

, toggleDownloads: function () {
    this.downloads.toggle();
  }

, _setTracker: function (elapsed, total) {
    if (this.ignoreTrackerUpdates) return;
    this.$('#song-time-meter .bar').slider('value', (elapsed / total) * 10000);
    this._setTimes(elapsed, total);
  }

, _setTimes: function (elapsed, total) {
    var elapsedFormatted = this._formatTime(elapsed)
      , totalFormatted   = this._formatTime(total);
    this.$('#song-time-remaining').text(elapsedFormatted + ' / ' + totalFormatted);
  }

, _setLoader: function (val) {
    this.$('#loading-indicator div').val(val).trigger('change');
  }

, _prevVolume: 0

, setVolume: function (volume) {
    this.volume = volume;
    if (this.current){
      soundManager.setVolume(this.current.get('id'), volume);
    }

    var spriteValue = 0;
    if (volume > 0) spriteValue ++;
    if (volume >= 50) spriteValue ++;
    if (volume === 100) spriteValue ++;
  }

, toggleMute: function () {
    var _prev = this.volume;
    this.setVolume(this._prevVolume);
    this.$('#vol-adjuster').slider('option', 'value', this._prevVolume);
    this._prevVolume = _prev;

    try {
        this._pauseTimer();
    } catch{
        //pass if timer was not yet set
    }
  }

, queueSong: function (song) {
    // Either immediately play or queue up
    if (this.playlist.collection.empty() && this.idle){
      this.play(song);
    } else {
      this.playlist.add(song);
    }
  }

, addSongToDownloads: function (song) {
    song.download();
  }

, addProfileTipToDownloads: function (profile) {
    profile.tip();
  }

, addAlbumToDownloads: function (album) {
    album.download();
  }

, play: function (song) {
    // Forces a song to start no matter what
    if (this.current !== undefined) {
      this.pause();
      // Stop loading current song if it is loading
      if (!this.current._loaded) {
        console.log('unloading');
        soundManager.unload(this.current.get('id'));
      }
    }
    this._setUIForPlayback(song);
    this._setUIForLoading();
    song.play();
    this.resume();
  }

, playPause: function () {
    this.paused ? this.resume() : this.pause();
  }

, pause: function () {
    this.$('#play-pause').removeClass('pause').addClass('play');
    soundManager.pause(this.current.get('id'));
    this.trigger('pause');
    this.paused = true;
    this._recordListen();
    this._resetTimer();
  }

, resume: function () {
    if (this.current === undefined) {
      if (this.playlist.collection.empty()) return;

      this.current = this.playlist.pop();
      this.play(this.current);
    } else {
      this.$('#play-pause').removeClass('play').addClass('pause');
      soundManager.resume(this.current.get('id'));
      this.trigger('resume');
      this.paused = false;
    }
    this._startTimer();
  }

, skipForward: function () {
    var next = this.playlist.pop();
    console.info('Recording listen for ' + this.current.get('id'));
    if (next !== undefined) {
      this._recordListen();
      this._resetTimer();
      this._startTimer();
      this.play(next);
    } else {
      this.pause();
      this._resetTimer();
      this._setUIForIdle();
      this.current = undefined;
    }
  }

, toggleVolume: function(){
    $('#playback-controls').toggleClass('volume-open');
}

// Private

, _setUIForLoading: function () {
    $('#song-time-remaining').hide();
    $('#loading-indicator').val(0).trigger('changed').show();
  }

, _setUIForLoaded: function () {
    $('#song-time-remaining').show();
    $('#loading-indicator').hide();
    if ($.browser.is_mobile){
      setTimeout(function(){
	$('#loading-indicator').hide();
      }, 3000);
    }
  }

, _setUIForPlayback: function (song) {
    // Whenever there's a song playing
    $('button[action="play"]').removeClass('spinning');
    this.$('#song-time-meter').show();
    this.$('#currently-playing').show();
    this.$('#player-traffic-light-buttons').show();
    this.$('#current-song-title').text(song.get('title'));
    this.$('#current-song-artist').text(song.get('artistName'));
    this.$('#artist-profile-img').attr('src', song.get('artwork'));
    this.$('#artist-profile-link').show();
    this.$('#artist-profile-link').attr('href', '/profile/' + song.get('artistKeyword'));
    this.$('#fan-current').attr('fanned', song.get('fanned'));
    this._setupTrafficLight(song);
    // Reset tracker to zero
    this._setTracker(0,1);
    this.idle = false;
    this._setTrackerCalc();
  }

, _setUIForIdle: function () {
    this.$('#song-time-meter').hide();
    this.$('#currently-playing').hide();
    this.$('#player-traffic-light-buttons').hide();
    this.idle = true;
  }

, _setupTrafficLight: function (song) {
    console.log("setting traffic lights for ", song);
    self = this;
    var price = song.get('priceVal');
    if (song.get('price')) {
      this.$('#download-current').show().text(
        (price === 0) ? 'Free' : '$' + song.get('price'))
      // hack
      this.$('#review-current').removeClass('last-button');
    } else {
      this.$('#download-current').hide();
      this.$('#review-current').addClass('last-button');
    }

    this.$('#fan-current, #review-current, #download-current')
      .attr('elem-id', song.get('id'))
      .attr('elem-title', song.get('title'))
      .attr('profile', song.get('artistKeyword'));
  }

, _recordListen: function() {
    if (this.secondsPlay > 0) {
        // its possible that recordListen is called twice when skipping forward
        // once with the correct value for seconds and again with a zero value
        // this ensure we skip the 0 value
        // its coded in this way to record listens on pause events as well
        // recording a listen and closing the browser still needs to be fixed
        try {
            // console.info('recording listen for -->', this.current.get('id'), 'for', this.secondsPlay, 'seconds');
            $.ajax({
                type: 'POST'
                // TODO change when fanning api goes up
                , url: '/song-listen/'
                , data: {
                    csrfmiddlewaretoken: csrfTOKEN
                , song_id:  this.current.get('id')
                , seconds: this.secondsPlay
                }, success: function() {}
            });
        }catch {}
    }
}

, _resetTimer: function () {
    // var self = this;
    try{
        if (!(this.timerId == null)) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
        this.secondsPlay = 0;
        // console.info('--> timer reset');
    }catch{}
  }

, _pauseTimer: function () {
    try{
        if (!(this.timerId == null)) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
        // console.info('--> timer paused', this.secondsPlay);
    }catch{}
  }

, _startTimer: function () {
    try{
        var self = this;
        if (this.timerId == null) {
            this.timerId = setInterval(function() {
                self.secondsPlay++;
                // console.info('--> time at ', self.secondsPlay);
            }, 1000);
        }
    }catch{}
  }

, _initializePlaylist: function () {
    var self = this
      , playlistQueue = new PlaylistQueue([], {
          url: APIROOT + 'queues/playlist'
        }).attachToCounter(this.$playlistCounter);

    // Initialize the play and download queues

    this.playlist = new Playlist({
      collection: playlistQueue
    });

    this.playlist.collection.fetch({ success: function () {
      self.playlist.render();
    }});
  }

, _initializeDownloads: function () {
    var self = this;

    var musicUploadDownloadQueue = new MusicUploadDownloadQueue([], {
        url: APIROOT + 'queues/downloads'
      }).attachToCounter(this.$downloadsCounter);

    this.downloads = new DownloadQueue({
      collection: musicUploadDownloadQueue
    });

    this.downloads.collection.fetch({
      success: function () {
        self.downloads.render();
    }});
  }

, _initializeLoader: function () {
    this.$('#loading-indicator div').knob({
      width: 14
    , fgColor: 'rgba(255,255,255,1)'
    , bgColor: 'rgba(255,255,255,0.2)'
    , displayInput: true
    , thickness: 0.2
    , readOnly: true
    });
  }

, _initializeTracker: function () {
    var self = this;

    this.on('progress', function (elapsed, total) {
      self._setTracker(elapsed, total);
    });

    var $bar = this.$('#song-time-meter .bar');
    $bar.slider({
      orientation: 'horizontal'
    , range: 'min'
    , min: 0
    , max: 10000
    , start: function () {
        // omg theyre dragging
        $(document).on('mousemove.tracker-preview', function () {
          var ratio = $bar.find('.ui-slider-range').width() / $bar.width(),
              totalTime = self.current._sound.durationEstimate;
          self._setTimes(totalTime * ratio, totalTime);
        });
        self.ignoreTrackerUpdates = true;

      }
    , stop: function (event, ui) {
        // omg they stopped dragging
        var posn = (ui.value / 10000) * self.current._sound.durationEstimate;
        soundManager.setPosition(self.current.get('id'), posn);
        $(document).off('mousemove.tracker-preview');
        self.ignoreTrackerUpdates = false;
      }
    });

    $bar.on('mousemove', function () {

    });
  }

, _initializeVolume: function () {
    var self = this;

    this.$('#vol-adjuster').slider({
      orientation: 'horizontal'
    , range: 'min'
    , min: 0
    , max: 100
    , value: 75
    , slide: function (event, ui) {
        self.setVolume(ui.value, true);
      }
    });
  }

, _setTrackerCalc: function () {
    var leftHalf = this.$('#open-play-queue').outerWidth() +
                   this.$('#playback-controls').outerWidth()
      , rightHalf = this.$('#open-download-queue').outerWidth() +
                    this.$('#player-traffic-light-buttons').outerWidth();


    var otherElementsWidth = leftHalf + rightHalf;

    this.$('#song-and-tracker').css({
      width: 'calc(100% - ' + otherElementsWidth + 'px)'
    , left: leftHalf + 'px'
    });
  }

, _formatTime: function (ms) {
    ms /= 1000;
    var mins = Math.floor(ms / 60)
      , seconds = Math.round(ms % 60);

    if (seconds === 60){
      seconds = 0;
      mins ++;
    }

    var minsString = '' + mins
      , secsString = '' + seconds;

    if (secsString.length == 1) secsString = '0' + secsString

    return minsString + ":" + secsString;
  }

, _soundManagerFlashWarning: function () {
    console.log('Flash warning');
  }

, _putUpPendingDownload: function () {
    this._takeDownPendingDownload();

    $('.pending-download').addClass('pending-download--visible');
    var periods = 3;
    this._pendingDownloadInterval = setInterval(function () {
      if (periods == 3) {
        periods = 0;
      } else {
        periods ++;
      }
      var text = 'preparing download';
      for (var i = 0; i < periods; i ++) {
        text += '.';
      }
      $('.pending-download').text(text);
    }, 300);
  }

, _takeDownPendingDownload: function () {
    clearInterval(this._pendingDownloadInterval);
    $('.pending-download').removeClass('pending-download--visible');
  }

});

$(document).ready(function(){
  hearo.player = new MusicPlayer()
});
