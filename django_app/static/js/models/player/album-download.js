window.AlbumDownload = Album.extend({

  initialize: function () {
    var self = this;

    this.listing = new AlbumDownloadListing({ model: this });

    Album.prototype.initialize.apply(this, arguments);
  }

, remove: function () {
    hearo.player.downloads.collection.remove(this);
  }

, toJSON: function () {
    var self = this;
    console.log('cover', this.get('cover'));
    return {
      title: this.get('title')
    , price: this.get('price')
    , cover: this.get('cover')
    , songcount: this.get('songs').length
    }
  }

, _counterValue: function () {
    return this.get('songs').length
  }

});
