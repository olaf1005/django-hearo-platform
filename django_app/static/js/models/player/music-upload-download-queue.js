window.MusicUploadDownloadQueue = hearo.Collection.extend({

  model: function (attrs, options) {
    if (attrs.type == 'song'){
      return new SongDownload(attrs, options);
    } else if (attrs.type === 'album'){
      return new AlbumDownload(attrs, options);
    } else if (attrs.type === 'profile'){
      return new ProfileTip(attrs, options);
    } else{
      throw "collection type must a known type (song, album, or profile) not " + attrs.type;
    }
  }

, initialize: function () {
    this.on('remove', function (elem) {
      this.APICall({
        type: 'DELETE'
      , url: 'queues/downloads/' + elem.get('type') + '~' + elem.get('id')
      }).on('success', function () {
        elem.listing.$el.remove();
      });
    });

    this.on('add', function (songDownload) {
      console.log(songDownload);
    });
  }

, empty: function () {
    return this.models.length === 0;
  }

, toJSON: function () {
    return this.models.map(function (item) {
      return item.toJSON();
    });
  }

});
