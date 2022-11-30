
window.ProfileTipListing = hearo.View.extend({

  partial: 'profile-tip-item'

, events: {
      'click .delete' : 'remove'
    , 'change .nyp-input' : 'updatePriceVal'
  }

, remove: function () {
    this.model.remove();
  }

, updatePriceVal: function (e) {
    var priceVal = ( +$(e.target).val() ); //typecast to number

    if (isNaN(priceVal) || priceVal < 0) {
      $(e.target).val("");
      return false;
    }

    this.model.set( {
         'priceVal':priceVal
        ,'price':priceVal.toFixed(2)
    } );
}

});
