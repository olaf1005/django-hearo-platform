hearo.Collection = Backbone.Collection.extend({

  APICall: hearo.mixins.APICall

, attachToCounter: function ($counter) {
    this.on('add', function (object) {
      $counter.counterIncrement(object.counterValue());
    });

    this.on('remove', function (object) {
      $counter.counterDecrement(object.counterValue());
    });

    return this;
  }

, render: function ($parent) {
    this.models.forEach(function (model) {
      try{
	model.listing.render($parent);
      } catch(err){
	console.log(err);
      }
    });
    return this;
  }

, counterLength: function () {
    return this.models.reduce(function (a, b) {
      return a + b.counterValue();
    }, 0);
  }

});
