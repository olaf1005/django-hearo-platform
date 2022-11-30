(function() {
  
  hearo.lightbox = {
    queue: [],
    open: function() {
      $("#darkness").show()
      hearo.lightbox.showContent();
      setTimeout(function() {
        $("#darkness").css("opacity", 1.0).one("click", function() {
          hearo.lightbox.close();
        });
      }, 1);
      $(document).on("keyup.lightbox", function(e) {
        if (e.which == 37){
          hearo.lightbox.left();
        }
        if (e.which == 39){
          hearo.lightbox.right();
        }
        if (e.which == 27){
          // Esc
          hearo.lightbox.close();
        }
        $(document).off("keyup.lightbox");
      });
    },
    close: function() {
      $("#darkness").css("opacity", '');
      setTimeout(function(){
        $("#darkness").hide();
        hearo.lightbox.empty();
      }, 200);
      $(document).off("keyup.lightbox");
    },
    empty: function() {
      $("#darkness #focus-element").empty();
    },
    left: function(){
      if (!hearo.lightbox.nav) return;

      var queue = hearo.lightbox.queue;
      var ind = queue.indexOf(hearo.lightbox.current)
      if (ind == 0) {
        ind = queue.length - 1
      } else {
        ind -= 1;
      }
      hearo.lightbox.hideContent();
      setTimeout(function(){
        hearo.lightbox.openMethod($(queue[ind]));
      }, 200);
    },
    right: function(){
      if (!hearo.lightbox.nav) return;

      var queue = hearo.lightbox.queue;
      var ind = queue.indexOf(hearo.lightbox.current)
      if (ind == queue.length - 1) {
        ind = 0;
      } else {
        ind += 1;
      }
      hearo.lightbox.hideContent();
      setTimeout(function(){
        hearo.lightbox.openMethod($(queue[ind]));
      }, 200);
    },
    show: function($content, width, height) {
      hearo.lightbox.empty();

      hearo.lightbox.nav = (hearo.lightbox.queue.length != 1)

      $("#darkness #focus-element").append($content)

      if (width === undefined) width = $content.width();
      if (height === undefined) height = $content.height();

      $("#darkness #focus-element").css({
        "margin-top": (window.innerHeight / 2) - (height / 2) + "px",
        "width": width + "px"
      });

      if (hearo.lightbox.nav){

        $("#darkness .arrow").show().css({
          top: (window.innerHeight / 2) - (42 / 2) + "px"
        });

        $("#darkness .arrow.left").css({
          left: (window.innerWidth / 2) - (width / 2) - 50 + "px"
        }).one("click", function(e) {
          e.stopPropagation();
          hearo.lightbox.left();
        });

        $("#darkness .arrow.right").css({
          right: (window.innerWidth / 2) - (width / 2) - 50 + "px"
        }).one("click", function(e) {
          e.stopPropagation();
          hearo.lightbox.right();
        });
      } else {
        $("#darkness .arrow").hide();
      }

      hearo.lightbox.open();
    },
    hideContent: function() {
      $("#darkness").addClass("hidden");
    },
    showContent: function() {
      $("#darkness").removeClass("hidden");

      $("#darkness #focus-element").one("click", function(e) {
        e.stopPropagation();
        hearo.lightbox.right();
      });
    }
  }

}());
