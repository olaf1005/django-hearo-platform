
window.ProfileTip = Profile.extend({

  initialize: function () {
    var self = this;

    this.listing = new ProfileTipListing({ model : this });

    Profile.prototype.initialize.apply(this, arguments);
  }

, remove: function () {
    hearo.player.downloads.collection.remove(this);
  }

, toJSON: function () {
    return {
      name: this.get('name')
    , artwork: this.get('artwork')
    , price: this.get('priceVal')
    }
  }
, _counterValue: function () {
    return 1;
  }

});
