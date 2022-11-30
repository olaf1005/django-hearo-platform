hearo.views.Filters = hearo.View.extend({

  el: '#filters-mask'

, initialize: function () {
    this.$('#main-toggle ul').earl({
      callbacks: {
        select: this._setToggle.bind(this)
      }
    });

    if (localStorage.getItem('filters') === 'open') this.toggle();

    this._setupAutocompleteSearch();
    if (hearo.directory !== undefined) {
      var filters = hearo.directory.filters;
    }else{
      var filters = {noun: ['artists', 'albums', 'songs']};
    }
    // fix for map enable disable
    var url = window.location.toString().match(/[^\?]*/)[0];
    if (url.indexOf('map') != -1) {
        filters['noun'].push('map');
    }

    this._filters = new Backbone.Model(filters);
    // Another level of filtration if the noun is "music"
    this.musicFilters = new Backbone.Model({
      // TODO un-hardcode this when URLs support music filters.
      ranking: 'hottest'
    , time:    'all'
    , price:   'all'
    });
    this._initializeState();
    this._filters.on('change', this._change.bind(this))
    this._setupMusicDropdowns();
    this._setupNounFilters();

    var self = this;

    //listen for click away from open filters
    $(document).on('click','body',function(e){
      var container = $("#filters-mask");
      var searchbar = $("#search-bar");
      var trigger = $("#open-filters");
      if (!container.is(e.target)
        && !trigger.is(e.target)
        && container.has(e.target).length === 0
        && container.hasClass('open')
        && !searchbar.is(e.target))
      {
        self.close()
      }
    })

    // listen for scroll (except on mobile since keyboard gets in the way and
    // would cause filters to close)
    if (!$.browser.is_mobile){
      $(window).on('scroll', function(e){
        self.close();
      });
    }
  }

, events: {
    'click button.sliding-sidebar__close': 'close'
  }

, _toURL: function (cb) {
    // TODO optimization: Make the URL call and the actual data call into a single call
    $.get('/map/url-for/', this._filters.toJSON(), cb);
  }

, _initializeState: function () {
    this.setNoun(this._filters.get('noun'));
    this.setLocation(this._filters.get('location'));
    this.setGenre(this._filters.get('genre'));
    this.setInstrument(this._filters.get('instrument'));
  }

, _change: function () {
    this._toURL(function (path) {
      var locationParts = window.location.toString().split('?')
        , newLocation = locationParts[0].replace(new RegExp(window.location.pathname + '$'), path);

      if (locationParts.length == 2) {
        newLocation += '?' + locationParts[1];
      }

      var pathPart = path.substring(1, path.length-1).replace('-', ' ');
      var title;

      if (pathPart != "/") {
         title = pathPart + ' - Tune.fm';
      } else {
         title = "Discover new music on tune.fm";
      }

      History.replaceState({
        artistDating: true
      }, title, newLocation);
      if (hearo.listings !== undefined) {
          hearo.listings.render({offset: 0});
      }
    }.bind(this));
  }

, _setToggle: function (el, option) {
    option = option.toLowerCase();
    this.$('#filters').attr('toggle', option);
    this._filters.set('noun', option);
  }

, setSearchQuery: function (query) {
    if (query === '') {
      hearo.utils.location.removeSearchKey('q');
    } else {
      hearo.utils.location.setSearchKey('q', query)
    }
    hearo.listings.render({offset: 0});
  }

, toggle: function () {
    this.$el.toggleClass('open');
    if(this.$el.hasClass('open')){
      localStorage.setItem('filters', 'open');
    }else{
      localStorage.setItem('filters', 'closed');
    }
  }

, open: function () {
    if(!this.$el.hasClass('open')){
      localStorage.setItem('filters', 'open');
      this.$el.addClass('open');
    }
  }

, close: function () {
    this.$el.removeClass('open');
    localStorage.setItem('filters', 'closed');
  }

// THE FOUR BIG FILTERS

, get: function (key) {
    return this._filters.get(key);
  }

, setNoun: function (noun) {
    // default enabled nouns
    noun = noun ? noun : ['artists', 'albums', 'songs'];
    this._filters.set('noun', noun);
  }

, setLocation: function (loc) {

  if (loc) {
    // Takes a location key (from URL)
    this._filters.set('location', loc);
    this.$('#search-location').val(loc);
    if(typeof hearo.map !== 'undefined'){
      try{
        hearo.map.selectLocation(loc)
      }catch(err){ }
      var coords = hearo.map.locations[loc];
    }
  } else {
    this._filters.unset('location');
    this.$('#search-location').val('');
  }
  }

, setGenre: function (genre) {
    if (genre) {
      this._filters.set('genre', genre);
      this.$('#search-genre').val(genre);
    } else {
      this._filters.unset('genre');
      this.$('#search-genre').val('');
    }
  }

, setInstrument: function (instrument) {
    if (instrument) {
      this._filters.set('instrument', instrument);
      this.$('#search-instrument').val(instrument);
    } else {
      this._filters.unset('instrument');
      this.$('#search-instrument').val('');
    }
  }

// Music settings

, setRanking: function (ranking) {
    ranking = ranking.toLowerCase();
    this.$('#music-filters').toggleClass('time-option-hidden', ranking !== 'hottest');
    if (this.musicFilters.get('ranking') != ranking){
      this.musicFilters.set('ranking', ranking);
      this._change()
    }
  }

, setTimePeriod: function (timePeriod) {
    timePeriod = timePeriod.toLowerCase();
    if (this.musicFilters.get('time') != timePeriod){
      this.musicFilters.set('time', timePeriod);
      this._change()
    }
  }

, setPrice: function (price) {
  if(typeof price !== 'undefined'){
    price = price.toLowerCase();
    if (this.musicFilters.get('price') != price){
      this.musicFilters.set('price', price);
      this._change();
    }
  }
  }

// helpers

, toHashTags: function () {
    var tags = ['music'];
    ['location', 'genre', 'instrument'].forEach(function (key) {
      var val = this._filters.get(key);
      if (val !== undefined) {
        tags.unshift(val.replace(/,.*$/,'').replace(/[^\w]/,''));
      }
    }.bind(this));

    return tags;
  }

, _setupMusicDropdowns: function () {
    this.dropdowns = {
      ranking: new hearo.components.Dropdown({
        el: '#ranking-dropdown',
      })
    , time: new hearo.components.Dropdown({
        el: '#time-dropdown'
      })
    , price: new hearo.components.Dropdown({
        el: '#price-dropdown'
      })
    }

    this.dropdowns.ranking.on('change', this.setRanking.bind(this));
    this.dropdowns.time.on('change', this.setTimePeriod.bind(this));
    this.dropdowns.price.on('change', this.setPrice.bind(this));
  }
, _setupNounFilters: function(){
    var self = this;

    var nouns = self._filters.get('noun');

    $('#noun-filters li').parent().children('li').each(function(i, el){
      // if noun is to be selected select it
      if (nouns.indexOf($(el).attr("data-val")) != -1){
        $(el).removeClass('off').addClass('on');
      }
    });

    // setup onclick handler
    // prevent double click
    //$('#noun-filters li').unbind('click');
    $(document).off('click', '#noun-filters li');
    $(document).on('click','#noun-filters li',function(){
    //$('#noun-filters li').click(function(){
      if(!$('#directory').length){
        ajaxGo("/");
      }
      $(this).toggleClass('off').toggleClass('on');

      var allOnVals = [];

      // now make sure all nouns which are 'on' are accounted for
      $(this).parent().children('li').each(function(i, el){
        // if the element doesn't have off set, push noun
        if (!$(el).hasClass('off')){
          allOnVals.push($(el).data('val'));
        }
      });

      // reset nouns
      self.setNoun(allOnVals.join('-'));

      // close for mobile since close on scroll is disabled
      if ($.browser.is_mobile){
        self.close();
      }


    })
  }
, _setupAutocompleteSearch: function () {
    var self = this;

    if(typeof hearo.map != 'undefined'){
      this.$("#search-location").localsuggest(hearo.map.locationKeys, {
        commas: false,
        floating: false,
        callback: function(x) {
          var coords = hearo.map.locations[x];
          this.setLocation(x);
          // close for mobile since close on scroll is disabled
          if ($.browser.is_mobile){
            self.close();
          }

        }.bind(this)
      });
    }

    /* Pull local autocomplete lists for genres and instruments */
    $.get('/get-autocomplete/', {
          info: '["instruments", "genres"]'
    }, function(data){
      $('#search-instrument').localsuggest(data.instruments, {
        commas: false,
        callback: function(x){
          self.setInstrument(x);
          // close for mobile since close on scroll is disabled
          if ($.browser.is_mobile){
            self.close();
          }
        },
        floating: false
      });
      $('#search-genre').localsuggest(data.genres, {
        commas: false,
        callback: function(x){
          self.setGenre(x);
          // close for mobile since close on scroll is disabled
          if ($.browser.is_mobile){
            self.close();
          }
        },
        floating: false
      });
    });
  }

});
