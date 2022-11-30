(function($){

  $.fn.counterIncrement = function (n) {
    var $self = $(this);

    // Disarm the animation
    $self.removeAttr('animating');

    // Ensure the correct orientation
    $self.attr('toggle', 'bottom');

    var current = parseInt($self.attr('value'), 10);

    $self.attr('value', current + 1);

    setTimeout(function () {

      // Arm the animation again
      $self.attr('animating', 'true');

      var $top    = $self.find('.counter-number--top')
        , $bottom = $self.find('.counter-number--bottom');

      $top.text(current + 1);
      $bottom.text(current);

      $self.attr('toggle', 'top');

      $self.css({
        width: $top.outerWidth() - 10 + 'px'
      });

      if (n !== undefined && n > 1) {
        setTimeout(function () {
          $self.counterIncrement(n - 1);
        }, 150 / n);
      }
    }, 1);
  }

  $.fn.counterDecrement = function (n) {
    var $self = $(this);

    // Disarm the animation
    $self.removeAttr('animating');

    // Ensure the correct orientation
    $self.attr('toggle', 'top');

    setTimeout(function () {

      var current = parseInt($self.attr('value'), 10);

      // Arm the animation again
      $self.attr('animating', 'true');

      var $top    = $self.find('.counter-number--top')
        , $bottom = $self.find('.counter-number--bottom');

      $top.text(current);
      $bottom.text(current - 1);

      $self.attr('value', current - 1);

      $self.attr('toggle', 'bottom');

      $self.css({
        width: $top.outerWidth() - 10 + 'px'
      });

      if (n !== undefined && n > 1) {
        setTimeout(function () {
          $self.counterDecrement(n - 1);
        }, 150 / n);
      }
    }, 1);
  }



}(jQuery));
