window.QueuedSong = Song.extend({

  initialize: function () {
    var self = this;

    this.listing = new QueuedSongListing({ model : this });

    window.Song.prototype.initialize.apply(this, arguments);
  }

, remove: function () {
    hearo.player.playlist.collection.remove(this);
  }

});
