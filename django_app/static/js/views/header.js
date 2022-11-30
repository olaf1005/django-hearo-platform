var Header = hearo.View.extend({

  el: '#header-bar'

, events: {
    'hover #filters-mask': 'openFilters',
    'click #open-filters': 'toggleFilters',
    'focus #search-bar': 'openFilters',
  }

, openFilters: function () {
    hearo.filters.open();
  }

, closeFilters: function () {
    hearo.filters.close();
 }

, toggleFilters: function () {
    // scroll to top when opening filters on mobile so we can view it in full
    if ($.browser.is_mobile){
      window.scrollTo(0, 0);
    }
    hearo.filters.toggle();
 }

});

$(document).ready(function(){
  hearo.header = new Header()
});

