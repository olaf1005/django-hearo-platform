(function() {

  var inAjaxCall = false;
  var page = 1;

  function getFanFeed() {

    inAjaxCall = true;
    page = page + 1;
    $.ajax({
      url: '/my-account/fan-feed/',
      data: { page: page },
      success: function(data) {
        inAjaxCall = false;
        $('.loader').hide();
        if(data.length > 1){
          var $container = $('#fan-feed');
          var $newElems = $( data );
          $container.append( $newElems );
          $container.masonry( 'appended', $newElems );
          setupLinks();
          $('#fan-feed').imagesLoaded(function(){
            $container.masonry( 'layout');
          });
        }else{
          //if the feed isn't empty, show finished message
          if($('#fan-feed li').length > 1){
            $('#feed-finished').show();
          }
          //set true so endlessScroll doesn't call getFanFeed anymore
          inAjaxCall = true;
        } 
      },
      error: function(data) {
        inAjaxCall = false;
        $('.loader').hide();
      }
    });
  }

  window.initFanFeed = function() {
    inAjaxCall = false;
    page = 1;

    var $container = $('#fan-feed');
    // initialize
    $container.masonry({
      itemSelector: 'li',
      gutter: 10
    });

    setTimeout(function(){$container.masonry('layout');},300);

    $(window).endlessScroll({
      fireOnce: false,
      fireDelay: false,
      loader: '',
      callback: function() {
        if (inAjaxCall) {
          return;
        }
        $('.loader').show();
        getFanFeed();
      }
    });
  }

}());
