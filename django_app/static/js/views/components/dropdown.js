var SELECTED_CLASS = 'dropdown-widget__option--selected';

hearo.components.Dropdown = hearo.View.extend({

  initialize: function () {
    // Defer this so the filters view learns about the first selection
    if($('#directory').length){
      setTimeout(function () {
        this.select({ target: this.$('.' + SELECTED_CLASS)[0]});
      }.bind(this), 1);
    }
  }

, events: {
    'click li': '_click'
  }

, _click: function (e) {
    console.log(e, this._isOpen);
    if (this._isOpen) {
      if (!this.options.no_redirect){
	if(!$('#directory').length){
	  ajaxGo("/");
	}
      }
      this.select(e);
      this.close();
    } else {
      this.open();
    }
  }

, _isOpen: false

, open: function () {
    this._isOpen = true;
    this.$el.addClass('is-open');
    setTimeout(function () {
      $(document).one('click', this.close.bind(this));
    }.bind(this), 1);
  }

, close: function () {
    this._isOpen = false;
    this.$el.removeClass('is-open');
  }

, select: function (e) {
    this.$('.' + SELECTED_CLASS).removeClass(SELECTED_CLASS);
    this.$el.prepend($(e.target));
    $(e.target).addClass(SELECTED_CLASS);

    this.value = $(e.target).attr('val');
    this.trigger('change', this.value);
  }

, hideIf: function (bool) {
    this.$el.toggle(bool);
  }

});
