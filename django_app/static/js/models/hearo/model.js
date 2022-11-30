hearo.Model = Backbone.Model.extend({
  
  APICall: hearo.mixins.APICall

, counterValue: function () {
    if (this._counterValue !== undefined) {
      if ((typeof this._counterValue) === 'function') {
        return this._counterValue();
      } else {
        return this._counterValue;
      }
    } else {
      return 1;
    }
  }

});
