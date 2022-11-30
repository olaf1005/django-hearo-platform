/* jquery_plugins.js
   all our plugins!
   */
/*global
  console,
  alert,
  jQuery,
  mousedown,
  uniqueid,
  csrfTOKEN,
  */

(function($){
  $.fn.listen = function(){
    return this.each(function(index, a){ setupLink(a); });
  }
  $.fn.linkify = function(options){
    var opts = $.extend({
      local : true
    }, options);

    var func = opts['local'] ? hearo.utils.local_linkify : hearo.utils.linkify;

    return this.each(function(){
      var $this = $(this);
      $this.html(func($this.html()));
      $this.find('a').listen();
    });
  }
  // short thing to make pressing enter do a callback
  $.fn.enter = function(callback){
    this.keydown(function(e){
      var code = e.keyCode || e.which;
      if(code === 13){ callback(); } // for enter button
    });
    return this;
  };

  $.fn.pretty_input = function(options){
    //defaults
    var settings = $.extend({
      'attr' : 'fillertext',        //where to scrape the text from
      'blur_class' : 'grey' // what class to give the unfocused text
    }, options);
    return this.each(function(){
      var txt, $this = $(this);
      txt = $this.attr(settings.attr);
      $this.focus(function(){
        if($this.val() === txt) {
          $this.val('');
          $this.removeClass(settings.blur_class);
        }
      }).blur(function(){
        if($this.val() === ''){
          $this.val(txt);
          $this.addClass(settings.blur_class);
        }
      });

      if ($this.val() === '' || $this.val() === txt){
        $this.addClass(settings.blur_class).val(txt);
      }
    });
  };

  $.fn.tab_it = function(options){
    //defaults
    var all, ops = $.extend({
      'hidden_class' : 'unselected',
      'shown_class' : 'selected',
      'click_callback': function(){} // for extra stuff
    },options);
    all = this;
    return this.each(function(){
      var $this = $(this);
      $this.click(function(e){
        ops.click_callback(e);
        if(! $this.hasClass(ops.shown_class)){
          all.addClass(ops.hidden_class).removeClass(ops.shown_class).each(function(){
            $("#"+$(this).attr('for')).hide();
          });

          $this.addClass(ops.shown_class).removeClass(ops.hidden_class);
          $("#"+$this.attr('for')).show();
        }
      });
    });
  };

  $.fn.hover_display = function(options){
    var keep, ops = $.extend({
      'to_display' : this,
      'hoverable_elts' : this,
      'delay' : 100
    },options);
    keep = false;
    ops.hoverable_elts.mouseover(function(){
      keep = true;
      ops.to_display.show();
    }).mouseleave(function(){
      keep = false;
      setTimeout(function(){
        if(!keep){ops.to_display.hide();}
      },ops.delay);
    });
  };

  /*
     hearo UI elements
     */

  $.fn.untouchable = function(uid){
    var $this = $(this);
    $this.addClass('noselect').find('input').on('focus.' + uid, function(){
      $(this).blur();
    });
    return $this };

    $.fn.touchable = function(uid){
      var $this = $(this);
      $this.removeClass('noselect').find('input').off('focus.' + uid);
      return $this };

      $.fn.lift = function(e){
        var $this = $(this), $clone = $this.clone(), offset = $this.offset();
        $clone.css({
          position: 'fixed',
          width: $this.outerWidth(),
          background: $this.css('background'),
          top: e.clientY - 10,
          left: e.clientX - 20,
        }).appendTo($('body'));
        $this.hide().attr('lifted');
        return $clone; };


        /*
         * Give this a $rolemodel jQ object and an object of css attrs.
         * Will copy keys from attrs form $rolemodel to $this.
         *
         * If value for key in attrs is a function, will apply that to the attr
         * before copying it to $this.
         *
         * NOTE: In this version functions must work only on ints.
         *
         * Example:
         * $('.whatever').mimick($header,
         *      { height: null, 'font-size': function(val){ return val + 10 }}
         * This will give $('.whatever') the height of $header and its font-size + 10
         */

        $.fn.mimick = function($rolemodel, attrs){
          var $this = $(this), val;

          for (var key in attrs){
            if (attrs.hasOwnProperty(key)){
              val = $rolemodel.css(key);
              if (typeof attrs.key === 'function'){
                /* Apply the modifier function if it exists */
                val = attrs.key(val);
              }
              $this.css(key, val);
            }
          }

          return $this;
        };

        $.fn.inline_edit = function(callback, modify){
          var $this = $(this), $input = $('<input type="text" class="inline-edit" />');

          /* Clean up the mess, do something with the value. */
          var reset = function(){
            $input.remove();
            $this.show();
            callback($input.val());
          };
          $this.hide().after($input);
          $input.val($this.text())
          .mimick($this, { 'font-size': null })
          .enter(reset).focus().select();

          /* Optional function for making extra configurations to the input field. */
          if (modify !== undefined){
            modify($input);
          }
          return reset;
        };

        /*
           Abstraction for inline editing Edit/Save button with callback.

           $target is an element whose value we are editing. Gets turned into an
           input field then the button is pushed.

           ajaxcall is a function that should commit the new val to the backend.

           modify (optional) is a function that gets called on the input field
           to modify it however we wish.
           */
        $.fn.inline_edit_button = function($target, ajaxcall, modify){
          var $this = $(this), reset, defaultVal = $this.attr("defaultval");

          $(this).click(function() {
            var text = $this.text(),
            callback = function(val) {
              $target.text(val);
              ajaxcall(val);
              $this.text(defaultVal);
            }

            if (text === defaultVal){
              reset = $target.inline_edit(callback, modify);
              $this.text('Save');
            } else if (text === 'Save'){
              $this.text(defaultVal);
              reset();
            }
          });
        };

        /*
           $.draggable
           Give an item drag-and-drop.

Options:
boundaryParent: the higher-level element inside which this element is constrained. Defaults to this element's direct parent.
x: (bool) Movable along x-axis?
y: (bool) Movable along y-axis?
autoPosition: (bool) Snap the draggable element to the top-left corner of the boundaryParent constraints as soon as this is called?
(true by default)
padding: (object of arrays) Put padding on inside the boundaryParent to further restrict movement.
Format: { x: [left, right], y: [top, bottom] }
callbacks: (object) Functions to fire off when things happen. Available callbacks are move, mouseup, mousedown.
Note: "move" runs every single time the position is updated, so a lot.
*/

        $.fn.draggable = function(options){
          var oldX, oldY, select, $this = $(this),
              uid = uniqueid(), /* d04K30rP2e-form id for handlers attached to this specific element */
              opts = $.extend({
                boundaryParent: $this.parent(),
                initiator: $this,
                x: true,
                y: true,
                startRightAway: false,
                autoPosition: true,
                dontAnimate: false,
                padding: { x: [0, 0], y: [0, 0] }
              }, options), bP_offset, dP_offset, mouseDownOnThis = false; /* bP = boundaryParent, dP = directParent */

              bP_offset = opts.boundaryParent == null ? { top: 0, left: 0 } : opts.boundaryParent.offset();
              dP_offset = $this.parent().offset();

              /* To avoid a TypeError, if this is called with no arguments */
              options = options || {};

              /* Ensure all callbacks are defined */
              opts.callbacks = $.extend({
                move: function(){},
                mouseup: function(){},
                mousedown: function(){},
                rawMove: function(){}
              }, options.callbacks);

              /* Auto-position this element unless instructed not to do so */
              if (opts.autoPosition){
                $this.css({
                  left: Math.round(bP_offset.left) - Math.floor(dP_offset.left) + opts.padding.x[0],
                  top: Math.abs(Math.round(dP_offset.top) - Math.floor(bP_offset.top)) + opts.padding.y[0]
                });
              }

              /* Put the mouseup event on the document so user can drag mouse off the element in one-axis mode */
              $(document).mouseup(function(e){
                oldX = oldY = undefined;
                $(document).off('mousemove.' + uid);
                $('body').touchable(uid);
                if (mouseDownOnThis) opts.callbacks.mouseup(e, $this);
                mouseDownOnThis = false;
              });

              /* Fire off the dragging when user first clicks on this element */

              var drag_action = function(){
                mouseDownOnThis = true; /* Ensure that mouseup doesn't fire on a false positive when use clicks on an option */
                opts.callbacks.mousedown();

                /* Make it so dragging over textareas doesn't focus on them, and over text doesn't select it */
                $('body').untouchable(uid);
                $(document).on('mousemove.' + uid, function(e){
                  var boundaries = opts.boundaryParent == null ? { left: 0, top: 0 } : opts.boundaryParent.offset(),
                  directParentOffset = $this.parent().offset(),
                  offset = $this.offset(),
                  changeX, changeY, offtop, offleft, offbottom, offright;
                  if (!mousedown) { console.log('f');return; }
                  if (oldX === undefined || oldY === undefined){
                    oldX = e.clientX;
                    oldY = e.clientY;
                    console.log('undefined');
                    return;
                  }

                  /* Determine how far off from the boundaries of boundaryParent this element is */
                  offleft = parseInt(offset.left - boundaries.left, 10); /* So this is how far off the left edge it is, etc... */
                  offtop = parseInt(offset.top - boundaries.top, 10);
                  if (opts.boundaryParent !== null){
                    offright = opts.boundaryParent.outerWidth() - $this.outerWidth() - offleft;
                    offbottom = opts.boundaryParent.outerHeight() - $this.outerHeight() - offtop;
                  }

                  /* See if we're hitting the boundaries. If so set the movement variables to 0. */
                  if (opts.x){
                    changeX = e.clientX - oldX;
                    if (opts.boundaryParent != null){
                      if (offleft + changeX < opts.padding.x[0]) {
                        changeX = offleft * -1;
                      } else if (offright - changeX < opts.padding.x[1]) {
                        changeX = offright;
                      }
                    }
                  } else {
                    changeX = 0;
                  }

                  if (opts.y){
                    changeY = e.clientY - oldY;
                    if (opts.boundaryParent != null){
                      if (offtop + changeY < opts.padding.y[0]) {
                        changeY = offtop * -1;
                      } else if (offbottom - changeY < opts.padding.y[1]) {
                        changeY = offbottom;
                      }
                    }
                  } else {
                    changeY = 0;
                  }

                  if (!opts.dontAnimate) {
                    /* Move this element! */
                    $this.animate({
                      left: '+=' + changeX + 'px',
                      top: '+=' + changeY + 'px'
                    }, 0);
                  }

                  /* Fire the move callback with the amounts moved */
                  opts.callbacks.move(e, {
                    x: changeX,
                    y: changeY
                  }, $this);

                  /* Save the current mouse position for the next time this runs */
                  oldX = e.clientX;
                  oldY = e.clientY;
                });
              };

              if (opts.startRightAway) drag_action();

              opts.initiator.mousedown(function(e){
                mouseDownOnThis = true;
                oldX = e.clientX;
                oldY = e.clientY;
                drag_action();
              });

              /* Waboom */
              return $this;
};

/*
   $.earl

   earl is our drag-and-drop slider for choosing between different options.
   It's in use at the top of Directory, and in the privacy settings in Dashboard.

Usage:
Bind earl to a <ul> element. Each <li> inside of it will become an option in the earl.
The <ul> element will become the slider, centered horizontally.

Options:
callbacks: Functions to fire when earl does things.
Right now there's only a select callback which runs whenever the user changes selections with earl.
The select callback is fed the text of the selection as its only parameter.
*/

$.fn.earl = function(options) {
  if ($(this).length == 0){ return $(this); }
  var $this = $(this), $container = $('<div></div>'), initialLeft,
      $knob, $mask, adjust_mask, select, snap,
      opts = $.extend({
padding: 10,
fontSize: 'inherit',
}, options);

opts.callbacks = $.extend({
select: function(){},
userselect: function(){}
}, options.callbacks);

if (opts.fontSize.match(/[a-z]/gi) === null){
  opts.fontSize += 'px';
}

/* This all just sets up the new DOM elements required */
$container.addClass('earl');
$this.addClass('basic_inset noselect').css({
padding: opts.padding + 'px 0px'
});
$this.find('li').css({
    'font-size': opts.fontSize,
    padding: '4px',
    });
$this.before($container);
$container.append($this);

/*
   Mask is the blue text you see inside the white earl knob. { overflow: hidden }
   This mask gets shifted in the opposite direction of the knob using the move callback in the draggable binding on the earl knob.
   This makes it look like it's not moving, and the earl knob is revealing it.
   */
$mask = $this.clone();
$mask.css({ left: $.browser.mozilla ? '0px' : '0' });

/* This is the move callback we're gonna feed into draggable */
adjust_mask = function(e, r){
  $mask.animate({ left: '-=' + r.x + 'px', top: '-=' + r.y + 'px' }, 0);
};

/* The white knob that highlights the selected text */
$knob = $('<div class="knob basic_border"></div>');


$mask.addClass('mask').removeClass('basic_inset').appendTo($knob);

/* Adjust the mask one pixel over because of some BS with odd pixel widths */
if ($this.outerWidth() % 2 === 1){
  $mask.animate({ left: '-=1px' }, 0);
}

/* When an option is explicitly clicked on, slide the knob over it and run the select callback */
select = function(opt, callback){
  var optOffset = opt.offset(), thisOffset = $this.offset(), containerOffset = $container.offset(),
  knobLeft = parseInt($knob.css('left').replace('px', ''), 10),
  changeX = (optOffset.left - 1 - thisOffset.left) +
    (thisOffset.left - containerOffset.left) - knobLeft,
  width = opt.outerWidth() - 1, text = opt.text();

  if ($.browser.mozilla){
    width += 2;
    changeX -= 2;
  }

  $knob.animate({
    left: '+=' + changeX + 'px',
    width: width
  }, 150, 'easeOutQuad');

  /* Compensate the mask the same way we do in adjust_mask up above */
  $mask.animate({
    left: '-=' + changeX + 'px'
  }, 150, 'easeOutQuad');

  /* Make the current selection retrievable later */
  $this.attr('value', text);

  if (callback){ opts.callbacks.select($this, text); }
};

/*
   When the user drags the knob and lets go, determine which is the closest option and snap to it.
   This is our mouseup callback for draggable.
   */
snap = function(){
  var distances = { }, nums = [ ], offset = $knob.offset(), keys, i;
  $this.children().each(function(i, x){
      var dist = parseInt(Math.abs(offset.left - $(this).offset().left), 10);
      distances[dist] = $(x);
      nums.push(dist);
      });
  var chosen = distances[nums.sort()[0]];
  select(chosen, true);

  setTimeout(function(){
      opts.callbacks.userselect(chosen.text());
      }, 150);
};

$this.find('li').click(function(){
    var $li = $(this);
    setTimeout(function(){
        opts.callbacks.userselect($li.text());
        }, 150);
    select($(this), true);
    });

/* Bind draggable to the knob with the callback methods we declared up above */
$knob.draggable({
autoPosition: false,
y: false,
boundaryParent: $this,
padding: {
x: [1, 1],
y: [0, 0]
},
callbacks: {
move: adjust_mask,
mouseup: snap
}
});

$knob.css({
height: $this.outerHeight() - ($.browser.mozilla ? 3 : 2)
}).appendTo($container);

/*
   We read the earl's value by reading a "value" attribute on the main ul.
   If that's predefined, select that option.
   */

setTimeout(function(){
    /* Calibration */
    $knob.css({
left: $this.offset().left - $container.offset().left
});
    $mask.css({
left: 0
});

    /* Go to default option if it's set, resort to first option */

    if ($this.attr('value') !== undefined){
    $this.children().each(function(){
        var $opt = $(this);
        if ($opt.text().toLowerCase() === $this.attr('value').toLowerCase()){
        return select($opt, true);
        }
        });
    } else {
    /* By default, select first child */
    select($this.children().first(), true);
    }
$knob.fadeIn(300);
}, ($.browser.mozilla ? 1000 : 0));

/* Waboom */
return $this;
};


/*
 * $.typeaction
 *
 * Wait until user has paused typing in a text field for given time (default 600ms) and fire provided callback
 */
$.fn.typeaction = function(callback, opts){
  // 48-57, 65-90
  opts = $.extend({ pause: 300 }, opts);
  var $this = this, timer;
  $this.on('keydown.typeaction', function(e){
      /* Ignore tab, so user can't tab through 10 fields and trigger 10 ajax calls */
      if (!(e.which == 9)) {
        clearTimeout(timer);
        timer = setTimeout(function(){
          callback($this);
        }, opts.pause);
      }
    });
    return this;
    };

    /*
     * $.spin
     *
     * Make something spin. Optional speed parameter, default = 3. 2 is slower, 4 is faster, etc.
     */

    $.fn.spin = function(speed){
      var $this = this, angle = 0, spinSpeed = speed || 3,
      interval = setInterval(function(){
        angle += spinSpeed;
        $this.rotate(angle);
      }, 2);
      this.attr('spin', interval);
    };

    /*
     * $.stopspin
     *
     * Undo $.spin
     */

    $.fn.stopspin = function(){
      clearInterval(this.attr('spin'));
      this.rotate(0);
      return this;
    };

    /*
     * $.button_spin
     *
     * Make a .blue button into a sick grey spinning one.
     * Returns one-time undo method.
     */

    $.fn.button_spin = function(){
      var $this = $(this), width = $this.width(), $white = $this.clone(),
      $spinner = $('<img src="/public/images/spinner.medium.anim.trans.gif" width="20" />');
      $white.empty().addClass('busy').css({
        width: width,
      }).append($spinner);
      $this.hide().after($white);
      $spinner.css({ margin: '0px auto' });

      return function(){
        $white.hide();
        $this.show();
        $spinner.stopspin();
      };
    };


    /*
     * $.loader
     *
     * Attach to input:text, puts a spinning loader on the far right.
     */

    $.fn.loader = function(){
    //   var $spinner = $('<div class="small spinner"></div>'),
    //   offset = this.offset(), width = this.outerWidth(),
    //   spinnerId = uniqueid();
    //   this.animate({
    //     width: '-=36px'
    //   }, 0).addClass('loading').attr('spinner', spinnerId);
    //   $spinner.appendTo($('body')).css({
    //     left: offset.left + width - 34 + 'px',
    //     top: offset.top + 14 + 'px',
    //     position: 'absolute'
    //   }).attr('id', spinnerId).spin();
    //   return this;
    };

    $.fn.stoploader = function(){
    //   this.animate({
    //     width: '+=36px'
    //   }, 0).removeClass('loading');
    //   $('#' + this.attr('spinner')).stopspin().remove();
    };

    /*
     * $.fog
     *
     * Cover a div in fog, making it unreachable.
     * Returns an undo method.
     */

    $.fn.fog = function () {
      var $this = $(this),
      width = $this.outerWidth(),
      height = $this.outerHeight(),
      offset = $this.offset(),
      $fog = $('<div class="fog"></div>').css({
        top: offset.top,
        left: '0px',
        height: height
      }).appendTo($('body')),
      $fog_inner = $('<div></div>').css({
        width: width,
        height: height
      }).appendTo($fog);

      return function(){
        $fog.remove();
      };
    };

    /* cloak & uncloak: fadeOut and fadeIn */

    $.fn.cloak = function(speed){
      if (speed === undefined){
        speed = 1000;
      }
      var $this = $(this);
      $this.addClass('cloaked').animate({
        opacity: 0
      }, speed);
    }

    $.fn.uncloak = function(speed){
      if (speed === undefined){
        speed = 1000;
      }
      var $this = $(this);
      $this.removeClass('cloaked').animate({
        opacity: 1
      }, speed);
    }

    /*
     * Bind to input input field.
     * Takes a string of characters or a regex, only allows characters matching to be typed in.
     */
    $.fn.whitelist = function(chars){
      var $this = $(this), validator;
      /* Two different cases for either a string or a regex chars input. */
      if (typeof chars == 'string'){
        chars = chars.split('');
        validator = function(character){
          return (chars.indexOf(character) !== -1);
        }
      } else if (chars instanceof RegExp){
        validator = function(character){
          return (character.match(chars) !== null);
        }
      }
      $this.keypress(function(e){
        /* Allow tab and backspace always. */
        if ([8,9].indexOf(e.which) !== -1) return true;
        /* Check if input matches chars */
        if (!validator(String.fromCharCode(e.which))) return false; });

        return $this;
    };

    /*
     * Nice visual collapse.
     * Basically hides the element but in a smooth vertical transition.
     *
     * No input or output.
     */
    $.fn.collapse = function(){
      $(this).each(function(){
        var $this = $(this);

        $this.attr('revert-height', $this.outerHeight() + 'px')
        .attr('revert-padding', $this.css('padding'))
        .attr('revert-margin', $this.css('margin'));

        $this.css({ opacity: 0 })
        .animate({
          height: '0px',
          margin: '0px',
          padding: '0px'
        }, 200, 'easeOutExpo');
      });
    };

    $.fn.ensureClass = function(classname, bool) {
      bool ?
        $(this).addClass(classname) :
        $(this).removeClass(classname);
    }

    /*
     * Undoes collapse, as you might guess.
     *
     * No input or output.
     */
    $.fn.uncollapse = function(callback){
      $(this).each(function(){
        var $this = $(this);

        $this.animate({
          height: $this.attr('revert-height'),
          margin: $this.attr('revert-margin'),
          padding: $this.attr('revert-padding')
        }, 200, 'easeOutExpo');

        setTimeout(function(){
          $this.animate({ opacity: 1 }, 50)
          /* Undo the height adjustment so it goes back to being flexible. */
          .css({ height: 'auto', margin: '', padding: '' });
        }, 200);

      });
    };




    /*
     * $.suggest
     *
     * Bind to input text. Pass in a list. Builds autocomplete list under the text field.
     */

    $.fn.suggest = function(list, opts){
      var opts = $.extend({
        callback: function(){},
        empty: "No suggestions.",
        floating: true
      }, opts);
      var $suggestlist = $('<div class="suggest' + (opts.floating ? "" : " inline") + '"></div>'),
      width = this.outerWidth(),
      height = this.outerHeight(),
      offset = this.offset(),
      $this = this,
      close_list = function(){
        $suggestlist.remove();
        $this.removeClass('suggest');
      }, make_option = function(option){
        var $choice = $('<div class="choice">' + option + '</div>');
        if (option === opts.empty){
          $choice.addClass('empty');
        } else {
          $choice.one('mousedown', function(){
            var choice = $(this).text(), val = $this.val(), prior_list;
            /* This part is weird */
            if (opts.commas){
              prior_list = val.match(/[\w\s\d]*,\s/g);
              $this.val((prior_list !== null ? prior_list.join('') : '') + choice + ', ');
            } else {
              $this.val(choice);
            }
            close_list();
            opts.callback(choice);
            if (opts.focusback){
              setTimeout(function(){
                $this.focus();
              }, 1);
            }
          });
        }
        try {
            // console.info("len", $suggestlist);
            $choice.appendTo($suggestlist);
        } catch {}
      };
      opts = $.extend({
        commas: false, cutback: 0, focusback: false }, opts);
        $('div.suggest').remove();
        if (list.length === 0){
          make_option(opts.empty);
        } else {
          $(list).each(function() {
            make_option(this);
          });
        }

        $suggestlist.css({
          left: offset.left,
          top: offset.top + height,
          width: width,
        })


        if (opts.floating){
          $suggestlist.appendTo($('body'));
        } else {
          $this.after($suggestlist);
        }

        $('div.choice').css({
          'font-size': $this.css('font-size'),
          padding: $this.css('padding')
        });

        this.blur(function(){
          setTimeout(function(){
            $suggestlist.hide();
            $this.removeClass('suggest');
          }, 1);
        }).focus(function(){
          $suggestlist.show();
          $this.addClass('suggest');
        }).addClass('suggest');
    };

    /*
     * $.autosuggest
     *
     * Wrapper for $.suggest that also uses $.typeaction. Provide and endpoint and it does the rest.
     *
     * Simply an extra layer of abstraction for the common UI of having a textbox that sends its value to an endpoint
     * and gets a suggestions dropdown built from a list returned.
     *
     * Input: endpoint (string) url to which we POST the val of the text field
     *        which will return the suggestions list.
     * Notes: The endpoint MUST return an array [ ] and not an object { }.
     *        The endpoint should listen for POST['value'], which is the value of the text field.
     */
    var oldalert = alert;

    // HACKY BUG FIX WITH JQUERY 1.8 and autosuggest
    // this means we cant do alert(1) however
    // this is here because if we type a single letter (it varies and
    // I haven't found the reason yet) say 'a', we get an alert(1)
    alert = function() {
      if (arguments[0] != 1) {
        oldalert.apply(window, arguments);
      }
    };

    $.fn.autosuggest = function(endpoint, callback){
      var $this = this;

      this.typeaction(function(){
        /* Put up a spinning loader while the call is being made */
        $this.loader();

        $.ajax({
          type: 'POST',
          url: endpoint,
          /* Automatically convert our response data to legible JSON */
          dataType: 'json',
          data: {
            'csrfmiddlewaretoken': csrfTOKEN,
            'value': $this.val()
          },
          success: function(data){
            $this.suggest(data, { callback: callback });
          },
          complete: function(){
            /* Take down the loader even if the call failed */
            $this.stoploader();
          }});});};

          $.fn.localsuggest = function(data, opts){
            var $this = this;
            /* Set commas to true to disragard the previously-listed values seperated by commas */
            opts = $.extend({
              commas: false,
              callback: function(){},
              floating: true
            }, opts);
            $this.typeaction(function(){
              var list = [ ],
              val = $this.val(),
              commalist = val.match(/[\w\s\d]*,/g);
              val = (commalist === null || opts.commas === false) ? val : (function(){
                try{
                  return val.match(/\,?\w+?$/g)[0];
                } catch(e) {
                  return '';
                }}());
                if (val.replace(', ', '').length < 1){
                  opts.callback('');
                  return $('div.suggest').remove();
                }
                $(data instanceof Array ? data : data()).each(function(i, el){
                  if (el.match(new RegExp(val, 'i')) != null){
                    list.push(this);
                  }
                });
                $this.suggest(list, {
                  commas: opts.commas,
                  cutback: val.length,
                  floating: opts.floating,
                  focusback: true,
                  callback: opts.callback
                });});};


                /*
                 * $.animate easing functions
                 * To use, provide name as a string for the optional third parameter.
                 * Example:
                 * $el.animate({ left: '+=10px' }, 500, 'easeOutElastic');
                 */

                jQuery.extend( jQuery.easing, {
                  def: 'easeOutExpo',
                  easeOutExpo: function (x, t, b, c, d) {
                    return (t===d) ? b+c : c * (-Math.pow(2, -10 * t/d) + 1) + b;
                  },
                  easeOutElastic: function (x, t, b, c, d) {
                    var s=1.70158, p=0,  a=c;
                    if (t===0){ return b;}  if ((t/=d)===1){ return b+c;}  if (!p){ p=d*0.3;}
                    if (a < Math.abs(c)) { a=c; s=p/4; }
                    else {s = p/(2*Math.PI) * Math.asin (c/a);}
                    return a*Math.pow(2,-10*t) * Math.sin( (t*d-s)*(2*Math.PI)/p ) + c + b;
                  },
                  easeOutElasticSofter: function (x, t, b, c, d) {
                    var s=1.70158, p=0,a=c;
                    if (t===0){ return b;}  if ((t/=d)===1){ return b+c;} if (!p){ p=d*0.5;}
                    if (a < Math.abs(c)) { a=c; s=p/4; }
                    else {s = p/(2*Math.PI) * Math.asin (c/a);}
                    return a*Math.pow(2,-10*t) * Math.sin( (t*d-s)*(2*Math.PI)/p ) + c + b;
                  },
                  easeOutQuad: function (x, t, b, c, d) {
                    return -c *(t/=d)*(t-2) + b;
                  },
                  easeInOutQuad: function (x, t, b, c, d) {
                    if ((t/=d/2) < 1){ return c/2*t*t + b;}
                    return -c/2 * ((t-1)*(t-2) - 1) + b;
                  }});

    }(jQuery));
