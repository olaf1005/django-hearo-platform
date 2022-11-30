hearo.utils.prettyAppend = function(htmlList, $target, opts) {// callback, doneCallback) {
  // Takes a list of HTML objects as strings
  // Appends them to target one at a time, with small delay between each
  // and fade-in effect. Just looks nice. :)

  if (htmlList.length == 0) return;

  opts = $.extend({
    afterEach: function () {}
  , onComplete: function () {}
  , autoScroll: false
  }, opts);

  var $rendered = $(htmlList[0]), counter = 0
    , images = $rendered.find('img'), waitUntil = images.length
    ;

  $(images).each(function(){
    $(this).on('load error', function(){
      ++ counter;
      if (counter == waitUntil){
        // Recursion happens after all images have been loaded so the transition looks nice.
        $rendered.animate({ opacity: '1' }, 70);
        var $play_button = $rendered.find('.song-play-button');
        if ($target[0].id == 'albums') {
          //bindPlayAlbum($play_button);
          true;
        } else {
          //bindPlaySong($play_button);
          true;
        }
        opts.afterEach($rendered);
        if (htmlList.length > 1) {
          hearo.utils.prettyAppend(htmlList.splice(1), $target, opts);
        } else {
          opts.onComplete();
        }
      }
    });
  });

  $target.append($rendered);
  $rendered.css("opacity", '0');
  //$rendered.find('button.fan, button.unfan').each(function(){ $(this).fanbutton() });
  setupLinks();
}
;
