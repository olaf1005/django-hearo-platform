window.AlbumDownloadListing = hearo.View.extend({

  partial: 'album-download-item'

, events: {
      'click .delete' : 'remove'
    , 'change .nyp-input' : 'updatePriceVal'
  }

, remove: function () {
    this.model.remove();
  }
  //Refactor this somehow - this is exactly the same for songs
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

