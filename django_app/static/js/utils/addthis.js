var self = hearo.utils.addthis = {
  DEFAULTS: {
    twitter: 'found some awesome music on @hearofm. '
  }

, passthrough: {
    twitter: function () {
      return self.DEFAULTS.twitter + self.hashtags();
    }
  }

, _hashtags: ['music']

, hashtags: function () {
    return self._hashtags.map(function (tag) {
      return '#' + tag
    }).join(' ');
  }

, setURL: function () {
    if (window.addthis !== undefined && window.addthis !== null) {
      addthis.update('share', 'url', window.location.toString().replace('localhost:8000','tune.fm'));
    }
  }

, setHashtags: function (hashtags) {
    self._hashtags = hashtags;
    try{
      self._updatePassthrough();
    }catch(err){}
  }

, _updatePassthrough: function (which) {
    addthis_share.passthrough.twitter.text = self.passthrough.twitter();
  }
}
;
