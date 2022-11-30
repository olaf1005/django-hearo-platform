hearo.utils.location = {
  setSearchKey: function (key, value) {
    var currentQueries = window.location.search;
    if (new RegExp(key + '=').test(currentQueries)) {
      // If we have this query already
      newQueries = currentQueries.replace(
        new RegExp(key + '=' + '[^&]*'), key + '=' + value)
    } else if (currentQueries === '') {
      // If we have no queries
      newQueries = '?' + key + '=' + value;
    } else {
      // If we have some other queries
      newQueries = currentQueries + '&' + key + '=' + value;
    }

    var newLocation = window.location.toString().match(/^[^\?]*/gi)[0] + newQueries;

    history.replaceState({}, window.location, newLocation);
  }

, getSearchKey: function (key) {
    var match = window.location.search.match(new RegExp(key + '=([^&]*)'));
    if (match && match.length > 1) {
      return match[1];
    }
  }

, removeSearchKey: function (key) {
    var newLocation = window.location.toString().replace(new RegExp(key + '=' + '[^\&]*'), '');

    if (/\?$/.test(newLocation)) {
      newLocation = newLocation.replace(/\?$/, '');
    }

    history.replaceState({}, window.location, newLocation);
  }
}
;

hearo.utils.updateMapCaption = function(e) {
  if (e === undefined) e = '#world-map .selected';
  // We might have a pure DOM element like event.target
  e = $(e);

  $('#count-number').html(e.attr('count'));
  $('#main-caption-location').html('in ' + e.attr('name'));
}
