import hearo_unittest as hu

from accounts.models import Profile
from media.models import Song, Album, Radio, MusicUpload
from .models import QueuedPlay


class QueuedPlayJsonifyTest(hu.TestCase):
    fixtures = ("one_musician", "one_song")

    def setUp(self):
        self.profile = Profile.objects.get(keyword="MusicianProfileId")
        self.request = hu.RequestFactory().get("/")
        self.request.user = self.profile.user

    def test_song_jsonify(self):
        fixture = QueuedPlay(profile=self.profile, song=Song.objects.all()[0])
        fixture.jsonify(self.request)

    def test_radio_jsonify(self):
        radio = Radio.objects.create(profile=self.profile)
        fixture = QueuedPlay(profile=self.profile, radio=radio)
        fixture.jsonify(self.request)

    def test_album_jsonify(self):
        album = Album.objects.create(title="foo", profile=self.profile, price=1)
        fixture = QueuedPlay(profile=self.profile, album=album)
        fixture.jsonify(self.request)
