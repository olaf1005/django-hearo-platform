window.QueuedSongListing = hearo.View.extend({

  partial: 'song-queue-item'

, events: {
    'click button.play-button' : 'play'
  , 'click button.delete'     : 'remove'
  }

, initialize: function () {
    this.listenTo(this.model, 'removed', function () {
      //console.log('remove el');
    });
  }

, play: function (e) {
    hearo.player.playlist.remove(this.model);
    hearo.player.play(this.model);
    e.stopPropagation();
  }

, remove: function () {
    this.model.remove();
  }

, renderOptions: {
    prepend: true
  }

});
