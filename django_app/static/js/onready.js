function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(document).ready( function() {

  var setup_DOM = function(contentclass){
   /*
    * Run the proper setup method based on what #content's classname is.
    * Example: on dashboard/profile, the classname is set to "dashboard profile".
    * We split that into two words, and drill down to the correct setup method: hearo.setup.dashboard.profile()
    */
    contentclass = (contentclass !== undefined) ? contentclass.split(' ') : '';
    if (contentclass.length == 1 && hearo.setup.hasOwnProperty(contentclass[0])){
      hearo.setup[contentclass[0]]();
    } else if (contentclass.length == 2 && hearo.setup.hasOwnProperty(contentclass[0]) && hearo.setup[contentclass[0]].hasOwnProperty(contentclass[1])){
      hearo.setup[contentclass[0]][contentclass[1]]();
    }
  }

  $.ajaxSetup({


    crossDomain: false

  , beforeSend: function(xhr, settings) {
      csrfTOKEN = getCookie('csrftoken');
      xhr.setRequestHeader("X-CSRFToken", csrfTOKEN);
    }

  , error: function(response){
    if (response.status == 401){
      loginRequired();
    }
  }

  , success: function(response) {

     /*
      * This handles AJAX-loaded pages (everything after initial load)
      * I/P: JSON with 'content', which is HTML to inject and 'contentclass',
      * which we give the content div as a class name. This gives us the proper
      * CSS rules and $(document).ready() setup method from hearo.setup
      */

      /* refreshScope gives us more control over how ajax page load works.
       *
       * The idea is simple. Give an <a> tag a "refresh-scope" attribute which is simply
       * a jQuery selector, like '#content[keyword="ArturSapek]'
       *
       * Upon loading via AJAX, the page will check look for an element in the old page that matches
       * the given selector. It also searches for one in the response html.
       *
       * If it finds both, it swaps only those. Otherwise the page is loaded normally.
       *
       * This simply lets us control what is being refreshed, so for example I can go from:
       *
       * /profile/ArturSapek
       *
       * to:
       *
       * /profile/ArturSapek/album/23/Underneath
       *
       * and only the media box will be changed, preserving the state of the rest of the page.
       *
       *
       * The selector probably needs to be specific or weird things can happen, but
       * this is a very open-ended functionality. Use it however you like :) but understand how it works!
       *
       */

    //default content div
    var contentElem = $('div#content').first();

    //content div used during artist dating
    var contentElemInner = $('div#content').last();

    var artistDating = History.getState().data.artistDating;

    // check if template passed title, otherwise use default
    var responseTitle =  response.title || hearo.defaultTitle;

    var refreshScope = History.getState().data.samePageRefreshScope,
        $scopeInOldPage = $(refreshScope),
        $scopeInResponse = $(response.content).find(refreshScope);

    if ($scopeInOldPage.length == 1 && $scopeInResponse.length == 1){
      // Replace only the specific element, because we've found one in both the old and new pages.
      $scopeInOldPage.replaceWith($scopeInResponse)
    } else {
      // Replace the entire page.
      contentElem.html(response.content);
    }

    if (!document.title){
      document.title = responseTitle;
    }

    /* working on remodeling here */
    setupListeners();
    refreshHeader(response);

    /* And finally let's run the setup method (effectively like $(document).ready(...)) */
    if (response.hasOwnProperty('contentclass')){
      setup_DOM(response.contentclass || '');
      /* This lets us use page-specific css with ajax-loaded pages */
      if(artistDating){
        contentElemInner.attr('class', response.contentclass || '');
      }else{
        contentElem.attr('class', response.contentclass || '');
      }
    }

    /* Apply pageclass if present, else clear */
    if (response.hasOwnProperty('pageclass')){
      /* This lets us use apply a class to #page which is above .content, Ex: about page */
      $('div#page').attr('class', response.pageclass || '');
    }else{
      if(!artistDating){
        $('div#page').attr('class','');
      }
    }

    // hack but seems to work, fixes issue that causes world map to appear
    // off center
    $('#world-map svg:first').resize();

  }});

  /* The setup method has to be run for the initial pageload, so here we go. */
  setup_DOM($('#content').attr('class'));

  setupListeners();

  // Preloading assets. Add urls to this list to preload images.
  $(['/public/images/ui/checkbox.checked.active.png',
     '/public/images/ui/checkbox.checked.hover.png',
     '/public/images/ui/checkbox.checked.png',
     '/public/images/ui/checkbox.unchecked.active.png',
     '/public/images/ui/checkbox.unchecked.hover.png',
     '/public/images/ui/checkbox.unchecked.png',
     '/public/images/ui/checkbox.checked.active.s.png',
     '/public/images/ui/checkbox.checked.hover.s.png',
     '/public/images/ui/checkbox.checked.s.png',
     '/public/images/ui/checkbox.unchecked.active.s.png',
     '/public/images/ui/checkbox.unchecked.hover.s.png',
     '/public/images/ui/checkbox.unchecked.s.png',
     '/public/images/ui/radio.unselected.png',
     '/public/images/ui/radio.unselected.active.png',
     '/public/images/ui/radio.unselected.hover.png',
     '/public/images/ui/radio.selected.png',
     '/public/images/ui/radio.selected.active.png',
     '/public/images/ui/radio.selected.hover.png',
     '/public/images/ui/delete.button.png',
     '/public/images/ui/delete.button.active.png',
     '/public/images/ui/delete.button.hover.png',
     ]).each(function(){
        var img = new Image();
        img.src = this;
    });

    // The following two functions bind the enter key from within the
    // email and password fields to the submitLogin button.

    $("#id_password, #id_email").enter(function(event){
      $("#submitLogin").click();
    });

    History.Adapter.bind(window, 'statechange', function() {
      var url, data;
      // if this is the same request whose response we've currently viewing, don't resend it (that's what the refresh button is for)
      // why necessary?
      if(currentRequestId  &&  currentRequestId === History.getState().data.requestId) { return; }

      url  = History.getState().url;
      data = History.getState().data;

      // google analytics, track state change as page view
      if (typeof(window.gtag) != 'undefined') {
        window.gtag('config', 'UA-174110339-1', {'page_path': new URL(url).pathname});
      }

      //dont process urls from pushState coming from Artist dating - listings.js
      if(data.artistDating != true){
        $.ajax(processUrl(url), data.ajaxData);
      }

    });

    hearo.filters    = new hearo.views.Filters()
    hearo.nounCounts = new hearo.views.NounCounts()
    hearo.search     = new hearo.views.Search()
    setupStripe();
    bindEditClickEvents();

    window.mousedown = false;

    // hack but seems to work, fixes issue that causes world map to appear
    // off center (this specifically fixes a resize issue, resize not moving
    // map to center)
    // $(window).resize(function(){
    //   console.info('resize');
    //   if ($('#world-map svg:first')[0]){
    //     $('#world-map svg:first')[0].width('');
    //   }
    // });


    $('#search-bar').bind('keypress',
      _.debounce(function() {
        if ($('#world-map').length === 0) {
          History.pushState({
            type: "link", // For google analytics
            httpReqType: "GET",
            data: null,
            samePageRefreshScope: null,
            requestid: nextRequest()
          }, null, '/?q=' + encodeURIComponent($('#search-bar').val()));
        }
      }, 800))


    $('#search-bar').bind('keypress', function(){
      hearo.filters.setLocation('');
      hearo.filters.setGenre('');
      hearo.filters.setInstrument('');
    });

    $('#search-location').bind('click', function(){
      $('#search-bar').val('');
      hearo.filters.setSearchQuery('');
    });
    $('#search-genre').bind('click', function(){
      $('#search-bar').val('');
      hearo.filters.setSearchQuery('');
    });
    $('#search-instrument').bind('click', function(){
      $('#search-bar').val('');
      hearo.filters.setSearchQuery('');
    });

}).mousedown(function(){ window.mousedown = true; }).mouseup(function(){ window.mousedown = false; });
