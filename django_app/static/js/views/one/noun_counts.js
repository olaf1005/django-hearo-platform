hearo.views.NounCounts = hearo.View.extend({

  partial: 'noun-counts'

, events: {
    'click .noun-count': '_select'
  }

, initialize: function () {}

, refresh: function (nounCounts) {
    if (!nounCounts) return;

    if (nounCounts.all < 1) {
      this.$el.hide()
    } else {
      this.$el.show()
      var renderData = {
        counts: []
      };

      for (var noun in nounCounts) {
        var count = nounCounts[noun];
        if (noun == 'all') {
          renderData.total_count = count;
        } else {
          if (count > 0) {
            renderData.counts.push({
              count: count
            , noun:  noun
            })
          } else if (count === 0) {
          }
        }
      }


      this.render($('#noun-counts'), { data: renderData });

      this.$('.noun-count').removeClass('selected');
      this.$('[data-noun="' + hearo.filters.get('noun') + '"]')
      .addClass('selected');
    }
  }

, _select: function (e) {
    var $nounCount = $(e.target).closest('.noun-count');
    if ($nounCount.hasClass('selected')) {
      hearo.filters.setNoun('people');
    } else {
      hearo.filters.setNoun($nounCount.data('noun'));
    }
  }
});
