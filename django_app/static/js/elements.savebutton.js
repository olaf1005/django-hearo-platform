/* dashboard save button */

(function(){

  var elapsed_time = 0, min_spin_time = 400, timer_interval;

  var savebutton = {
    spin: function(){
      elapsed_time = 0;
      var $save = $('button#save');
      $save.addClass('spinning');
      timer_interval = setInterval(function(){
        elapsed_time += 10;
      }, 10);
      return this;
    },
    revert: function(){
      if (elapsed_time < min_spin_time){ /* Wait at least min_spin_time before reverting. */
        setTimeout(savebutton.revert,
          /* Add some small random time so it doesn't feel fake */
          min_spin_time - elapsed_time + (500 * Math.random()));
          return;
      }
      var $save = $('button#save');
      $save.removeClass('spinning');
      clearInterval(timer_interval);
      return this;
    },
    show: function(){
      $('button#save').show();
    },
    hide: function(){
      $('button#save').hide();
    }
  };

 /*
  * global exports
  */

  hearo.elements.savebutton = savebutton;

}());
