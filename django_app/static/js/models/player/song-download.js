window.SongDownload = Song.extend({

  initialize: function () {
    var self = this;

    this.listing = new SongDownloadListing({ model : this });

    Song.prototype.initialize.apply(this, arguments);
  }

, remove: function () {
    hearo.player.downloads.collection.remove(this);
  }

, toJSON: function () {
    return {
      title: this.get('title')
    , price: this.get('price')
    }
  }

});
