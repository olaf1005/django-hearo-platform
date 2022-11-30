(function(){
  var pingIndex = 0;

  hearo.utils = {

    refreshSection: function(selector, success){
      // Given a jQuery selector or an Array of them, this reloads the page via ajax, extracts
      // the new content's item for those selectors, and replaces all the selectors with their updated states.
      // Selectors must always return ONE result.
      //
      // Success callback optional, called with the replaced jQuery object passed in.
      //
      // Very useful for dynamically reloading a page using templates.
      //
      // Recommended you use elements' ids that are guaranteed to be unique
      // and not weird specific strings of selectors that are not guaranteed to be
      // specific enough to be unique.

      var replace = function(selector, content) {
        var $captured = $(content).find(selector);
        if ($captured.length == 1){
          $("#content").find(selector).replaceWith($captured);
          if (success !== undefined) {
            success.call($captured, $captured);
          }
        }
        $('body').css({overflow: '', height: ''});
        if (window.hearo.listings){
          // if profile blocked loading listings renable now
          window.hearo.listings._pending = false;
        }
      }

      $.getJSON(document.location, { ajax: true }, function(data){
        if (selector == "*"){
          $("#content").html(data.content);
        } else {
          if (selector instanceof Array) {
            selector.map(function(s) {
              replace(s, data.content);
            });
          } else if (typeof selector === "string") {
            replace(selector, data.content);
          }
        }

        if (success !== undefined) {
          success($(data.content));
        }
      });
    },
    local_linkify : function(text){
      var pattern = /\/(download|profile|music|directory|my-account)(\/?.*)/
      var replace = "<a href='/$1$2'>/$1$2</a>";
      return text.replace(pattern,replace);
    },
    linkify : function(text){
      var pattern = /(HTTP:\/\/|HTTPS:\/\/)([a-zA-Z0-9.\/&?_=!*,\(\)+-]+)/i;
      var replace = "<a href=\"$1$2\" target=\"_blank\">$1$2</a>";
      return text.replace(pattern , replace);
    },
    //everything we want happening often, keep client in contact with server
    //MAKE SURE IF YOU ADD SOMETHING YOU DONT OVERWRITE ANY DATA IN THE REQUEST OR RESPONSE
    ping : function(callback){
      var calls = [];
      var download_id = hearo.pending_download;

      var urls = ['/mail/unread-count/'];
      if(download_id){ urls.push('/get-download-status/'); }

      $.ajax({
        type : "GET",
        url : "/ping/",
        data : {
          i: (pingIndex += 1),
          on_mail_page: $("#page_name").attr('value') === 'fanmail' ? 't' : 'f',
          now_count: $("#fanmail-envelope").text(),
          download_id : download_id,
          urls : JSON.stringify(urls)
        },
        dataType : 'json',
        success : function(response){
          fanmail.update_unread_messages(response);
          if(response.url){
              var form = $(createElem('form', { 'action': response.url }));
              $(document.body).append(form);
              form.submit();
              hearo.pending_download = false;
              hearo.player._takeDownPendingDownload();
          }
          if(callback){ callback(); }
        }
      });
    }
  }

}());
