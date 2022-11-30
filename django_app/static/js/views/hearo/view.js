hearo.View = Backbone.View.extend({

  mustache: function (name, attrs) {
    var template = $("script#partial-" + name).html();
    return Mustache.render(template, attrs);
  }

, render: function ($parent, options) {
    var old$el = this.$el;

    if (options === undefined) options = {};

    if (this.model !== undefined) {
      options = $.extend({
        data: this.model.attributes
      }, options);
    }

    if (this.renderData !== undefined) {
      options.data = this.renderData();
    }

    var $rendered = $(this.mustache(this.partial, options.data)).first();

    this.setElement($rendered);

    if (old$el !== undefined) old$el.replaceWith(this.$el);

    if (this.renderOptions.prepend) {
      this.$el.prependTo($parent || this.$parent);
    } else {
      this.$el.appendTo($parent || this.$parent);
    }

    return this;
  }

, renderOptions: {}

, APICall: hearo.mixins.APICall


});
