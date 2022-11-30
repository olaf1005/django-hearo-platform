/* ajaxify.js

*/


(function(){

    function setupPage(pagename) {
        var page;
        page = $("#" + pagename + "Page");
        page.click(function() {
            page.data("listening", true);
            page.click( function(e) {
                e.preventDefault();
                History.pushState({
                    type: pagename,
                    httpReqType: "GET",
                    data: null,
                    requestid: nextRequest()
                }, null, page.attr("href"));
            });
        });
    }

    function setupPages() {
        setupPage('profile');
        setupPage('jam');
        setupPage('feeds');
        setupPage('events');
    }
    function setupLink(a){
         var $a = $(a), id = $a.attr('id'), href = $a.attr('href') || ''; // Do this to not make a million jQuery objects at once, it's a bit faster
         if (! $a.is('a')) return;

         //ignore artist dating links while artist dating
         if( $('#modal-container').length && $a.hasClass('profile-ajax')) return;

         if (!($a.data("listening") ||
         $a.attr('target') == '_blank' ||
         href.indexOf("/logout") > -1 ||
         href.indexOf('http://') > -1 ||
         href.indexOf('mailto:') > -1 ||
         $a.hasClass('ajax') ||
         $a.hasClass('ui-slider-handle')) && ($a.attr("href"))) {

            $a.data("listening", true)
              // Unbind click before binding, some this can be called more than once without piling up listeners
             $a.unbind('click').click( function(e) {

                 e.preventDefault();

                 History.pushState({
                     type: id ? id : "link", // For google analytics
                     httpReqType: "GET",
                     data: null,
                     samePageRefreshScope: ($a.attr("refresh-scope") || null),
                     requestid: nextRequest(),
                     artistDating: ($a.attr("artist-dating") || false)
                 }, null, $a.attr("href"));
            });
        }
    }
    function setupLinks() {
        $("a").listen(); //defined in jquery_plugins
    }

    function setupForms() {
        $("form").each( function() {
            if(!$(this).data("listening")) {
                $(this).data("listening", true);
                if(this.id === "photoForm" || this.id === "songUploadForm" || this.id === "albumForm" ) { // Search
                    return;
                }
                $(this).submit(function(e) {
                    e.preventDefault();
                    var loc = $(this).attr("action");
                    History.pushState({
                        type: "form",
                        httpReqType: $(this).attr("method"),
                        data: $(this).serialize(),
                        requestid: nextRequest()
                    }, null, loc);
                });
            }
        });

        $('#login-form input').each(function(){
          $(this).enter(loginFunc);
        });
    }

    function setupAlbumTiles(){
        $('[revealalbum]').unbind().click(function(){
            var self = $(this),
                parent = self.parent(),
                id = self.attr('revealalbum');
            parent.find('[revealalbum]').hide();
            parent.find('[albumtracks="' + id + '"]').show();
        });
    }

    // function setupReviews(){



    // }

    // function setupDownloadButtons(){
    //   bindDownloadButton(".downloadSong", 'song');
    //   bindDownloadButton(".downloadAlbum", 'album');
    // }


    function setupPing(){
        var length = hearo.pending_download ? 5000 : 15000;
        setTimeout(function(){
            hearo.utils.ping(setupPing);
        }, length);
    }

    function setupListeners() {

        $("[fillertext]").pretty_input();

        //$('button.fan, button.unfan').each(function(){ $(this).fanbutton() });

        //setupFanButtons();

        //setupFandButtons();

        setupDropDown();

        setupLinks();

        setupForms();

        bindEditClickEvents();

        setupAlbumTiles();

        //setupDownloadButtons();

    }
    function setupDropDown() {
        var $accountMenu;
        //sets the hiding and the showing of the dropdown. Give it a timeout
        $("#accountInfo").hover_display({
            'to_display' : $(".header__account__dropdown"),
            'hoverable_elts' : $(".dropdown_hover")
        });

        $("#header__content").hover_display({
            'to_display' : $("#header__about__dropdown"), //hidden element
            'hoverable_elts' : $(".about_hover_trigger") //hover trigger
        });

        if ($.browser.is_mobile){
          // fix about button on mobile (hover is click)
          $(".about_hover_trigger").attr('href', '#');
        }

        $("header__content").hover_display({
            'to_display' : $("#login-form"), //hidden element
            'hoverable_elts' : $(".login_hover_trigger") //hover trigger
        });
    }

    /*
        so we put session info into the httpresponse in render_appropriately, which
        lets us "refresh" the header so to speak in this function
        whenever we refresh our header, we also want to update the (rarely used) globals sessionInfo
        right now (aug 9 2012) this is the only place they are defined, so don't worry about them too much

        this function is called from the default ajax call (ajaxSetup in onready.js), as well as any place
        where we want to do
    */
   function refreshHeader( response ) {
        if(response.session_info){
            if(response.session_info.profile){

                sessionInfo.cur_account = response.session_info.profile;
                sessionInfo.accounts = response.session_info.accounts;
                $("#currentAccountPhoto").attr("src", sessionInfo.cur_account.img_path);
                $("#accountInfo .imageLink, #navigation .profile a").attr("href", sessionInfo.cur_account.url);
                $("#navigation .profile, #accountInfo").show();

                $("#drop_down_name").text(sessionInfo.cur_account.short_name);
                $sa = $("#switchAccounts");
                $sa.empty();
                if(sessionInfo.accounts.length >= 2){
                    _.each(sessionInfo.accounts, function(ac){
                        $sa.append($(createElem('li')).append(createElem('a',{'href':ac.url+'/?switchid='+ac.id},ac.short_name)));
                    });
                }
                var mc = response.session_info.mail_count;
                if(mc > 0){
                       $("#fanmail-envelope").addClass('full-envelope').show().html(mc);
                }else{
		  $("#fanmail-envelope").removeClass('full-envelope').hide().html(mc);
		}

            }else{
                $("#navigation .profile, #accountInfo").hide();
		//find all the small fan buttons and give them a tooltip prompt to tell them to log in or join
                $('.small_fan_button').unbind('click').addClass('tooltiptop')
                    .append($(createElem('div', {className:'tooltip_description'})).css({'display':'none'}).text('Log in or join to fan!'))

            }

        }

    }

    //export

    window.setupLinks = setupLinks;
    window.setupLink = setupLink;
    window.setupListeners = setupListeners;
    window.refreshHeader = refreshHeader;
    window.setupLinks = setupLinks;
    //window.setupFandButtons = setupFandButtons;
    //window.setupFanButtons = setupFanButtons;

    window.setupPing = setupPing;

    //window.setupDownloadButtons = setupDownloadButtons;
}());
