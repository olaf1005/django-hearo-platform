
(function(){


  window.setAvgStars = function(avg) {
    // Round to the nearest half
    if (Math.round(avg) == Math.ceil(avg)){
      // If rounding it goes up, it's >= n.5 so keep the .5
      // Otherwise, ditch it and go to the next lowest ineger.
      if (Math.round(avg) != avg) {
        avg = Math.ceil(avg) - 0.5;
      }
    } else {
      // Otherwise, we're rounding down.
      // Check if n is closer to floor(n) or floor(n) + 0.5
      if (((Math.floor(avg) + 0.5) - avg) < 0.25) {
        avg = Math.floor(avg) + 0.5;
      } else {
        avg = Math.floor(avg);
      }
    }

    $('div.reviews-star').removeClass("set").removeClass("set-half");
    for (var i = 0; i <= avg; i += 0.5){
      if (Math.round(i) !== i){
        // If it's a half
        console.log('half', i, $('div.reviews-star[value="' + Math.floor(i + 1) + '"]')[0]);
        $('div.reviews-star[value="' + Math.floor(i + 1) + '"]').removeClass("set").addClass("set-half");

      } else {
        // If it's a whole
        console.log('whole', i, $('div.reviews-star[value="' + (Math.ceil(i) - 1) + '"]')[0]);
        $('div.reviews-star[value="' + i + '"]').removeClass("set-half").addClass("set");

      }
    }

  }

}());

