window.PlaylistQueue = hearo.Collection.extend({

  model: QueuedSong

, initialize: function () {
    this.on('remove', function(queuedSong) {
      this.APICall({
        type: 'DELETE'
      , url:  'queues/playlist~' + queuedSong.get('id')
      }).on('success', function () {
        queuedSong.listing.$el.remove();
      });
    });

    return this;
  }

, empty: function () {
    return this.models.length === 0;
  }

});
