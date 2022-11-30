window.DownloadQueue = hearo.View.extend({

  el: '#downloads'

, events: {
    'click .js-download-purchase' : '_purchase'
  }

, initialize: function () {
    var self = this
      , reset = _.debounce(function () {
       self.render();
     }, 100);

    this.collection.on('add remove change', reset);

    this.collection.fetch();

    this._loadCards();

    this.render();
  }

, partial: 'download-queue'

, render: function () {
    hearo.View.prototype.render.call(this);
    this.collection.render(this.$el.find('#downloads-content'));
  }

, renderData: function () {
    var total = this._totalPrice()
      , count = this.collection.counterLength();
    return {
      count: count - this._numTips()
    , empty: count === 0
    , total: total.toFixed(2)
    , free : total === 0
    , cards: this.cards
    , nocards: (this.cards === undefined ? true : this.cards.length === 0)
    , items: this.collection.toJSON()
    , open : this._open
    }
  }

, toggle: function () {
    this._open = !this._open;

    if (this._open) {
      this.$el.addClass('open');
      $('#pending-downloads').addClass('shoved-over-left');
    } else {
      this.$el.removeClass('open');
      $('#pending-downloads').removeClass('shoved-over-left');
    }
  }

, close: function () {
    this._open = true;
    this.toggle();
  }

, _purchase: function () {
    var self = this;
    self.render();
    $.ajax({
      type: 'POST'
      , url: '/payment/buy_songs'
      , dataType: 'json'
      , data: {
        csrfmiddlewaretoken: csrfTOKEN
        , card_token: this._chosenCard()
        , songs:      JSON.stringify(this._songPrices())
        , albums:     JSON.stringify(this._albumPrices())
        , tips:       JSON.stringify(this._tipValues())
      }
      , success: function (response) {
        self.$('button').removeClass('spinning');
        self.collection.fetch();
        // @todo
        // if user is only tipping need to show this
        hearo.pending_download = response.download_id
        self.close();
        setTimeout(function () {
          hearo.player._putUpPendingDownload();
        }, 450);
        self.$('button').addClass('spinning');
      }
      , error: function(response){
        var error = $.parseJSON(response.responseText).error;
        $('#download-error').text(error).show();
      }
    });

}

, _open: false

, add: function (song) {
    var self = this;

    this.collection.add(song);

    this.APICall({
      url: 'queues/downloads'
      , type: 'POST'
      , data: {
        id: song.get('id')
      }
    });
}

, _loadCards: function () {
    var self = this;
    // Load the user's credit cards
    this.APICall({
      url: 'my/cards'
    }).on('success', function(data) {
      self.cards = data;
      self.render();
    });
  }

, _chosenCard: function () {
    return this.$('#card-picker').find('option:selected').val();
  }

, _totalPrice: function () {
    return this.collection.models.reduce(function (a, b) {
      if (b.get('owned') == false || b.get('owned') == undefined){
	return a + b.get('priceVal');
      }
      return a;
    }, 0);
  }

, _songPrices: function () {
    var prices = {};
    this.collection.models.forEach(function (obj) {
      if (obj instanceof Song) {
        prices[obj.get('id')] = obj.get('priceVal')
      }
    });
    return prices;
  }

, _albumPrices: function () {
    var prices = {};
    this.collection.models.forEach(function (obj) {
      if (obj instanceof Album) {
        prices[obj.get('id')] = obj.get('priceVal')
      }
    });
    return prices;
  }

, _numTips: function () {
  var cnt = 0;
    this.collection.models.forEach(function (obj) {
      // need to check if this is actually a tip
      if (obj instanceof Profile) {
        cnt += 1;
      }
    });
    return cnt;
  }

, _tipValues: function () {
    var prices = {};
    this.collection.models.forEach(function (obj) {
      // need to check if this is actually a tip
      if (obj instanceof Profile) {
        prices[obj.get('id')] = obj.get('priceVal')
      }
    });
    return prices;
  }

});
