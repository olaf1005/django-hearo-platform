//
// Plugins that make bind appropriate listeners to common Hearo elements like the fan button.
//

(function($){
  
  $.fn.fanbutton = function(){
    // Make any button.red.fan with objid and objtype attributes into a functioning fan button.

    var $this = $(this),
        objid = $this.attr('objid'),
        objtype = $this.attr('objtype');
    
    // Make sure there is only one copy of this listener with unbind
    $this.unbind('click.fanbutton').on('click.fanbutton', (function(e) {
      e.stopPropagation();

      // Is this a fan button? False means it's an unfan button.
      var fan_action = $this.hasClass('fan');

      // Call either fan_this or unfan_this and swap "fan" and "unfan" classes.
      window[(fan_action ? '' : 'un') + 'fan_this'](objtype, objid, function() {

        // There may be more than one fan button for this entity in the DOM.
        // Query them by objtype and objid, then update them all at once.
        var buttons = $('button[fan_button="' + objtype + objid + '"]');

        $(buttons).each(function(){
          $(this).removeClass(fan_action ? 'fan' : 'unfan').addClass(fan_action ? 'unfan' : 'fan')
                 .removeClass(fan_action ? 'red' : 'transblack').addClass(fan_action ? 'transblack' : 'red')
                 .text(fan_action ? 'FAN\'D' : 'FAN');
        });
      });
    }));
  };

}(jQuery));
