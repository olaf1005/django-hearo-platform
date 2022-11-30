window.Playlist = hearo.View.extend({

  el: '#playlist-content'

, initialize: function () {
    var self = this;

    var reset = _.debounce(function () {
      self.render();
      hearo.player._setTrackerCalc();
    }, 100);

    this.collection.on('add remove change', reset);
  }

, render: function () {
    this.$el.empty();
    this.collection.render(this.$el);

    this.$el.parent().ensureClass('empty', this.collection.empty());
    $('body').ensureClass('songs-queued', !this.collection.empty());
    return this;
  }

, add: function (song) {
    var self = this;

    this.collection.add(song);

    // TODO Update w new API
    $.ajax({
      type: 'POST'
    , url: '/player/add-play'
    , data: {
        id: song.id
      , type:'song'
      , index: self.collection.length
      }
    , success: function () {}
    });
  }

, pop: function () {
    var first = this.collection.at(0);
    this.collection.remove(first);
    return first;
  }

, remove: function (song) {
    this.collection.remove(song);
  }

});
