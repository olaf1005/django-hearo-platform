hearo.views.Search = hearo.View.extend({

  el: '#search-bar'

, events: {
    'keyup': '_onKeyup'
  }

, initialize: function () {
    var self = this;
    this._onKeyup = _.debounce(function () {
      self._setSearchQuery();
    }, 800);

    var queryFromURL = hearo.utils.location.getSearchKey('q');
    if (queryFromURL !== undefined) {
      this.$el.val(decodeURI(queryFromURL));
    }
  }

, _setSearchQuery: function () {
    hearo.filters.setSearchQuery(this.$el.val());
  }

});
