(function () {

  _.forEachAsync = function (array, callback, delay) {
    if (!(array instanceof Array)) return;
    if (array.length === 0) return;

    var head = array[0]
      , tail = array.slice(1);

    callback(head);

    if (array.length === 1) return;

    setTimeout(function () {
      _.forEachAsync(tail, callback, delay);
    }, delay);
  }

}());
