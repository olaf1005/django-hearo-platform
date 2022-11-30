from django.test import TestCase

from accounts.models import Fan, Profile, Review, AlbumFanEvent, SongFanEvent
from activity.models import Feed
from events.models import Event
from mail.models import Message
from media.models import Album, Song
from player.models import Play

import datetime


class FeedTest(TestCase):
    def setUp(self):
        self.user1 = Profile.objects.create(
            name="Felipe Coury",
            short_name="Felipe",
            default_download_format="mp_320",
            keyword="fcoury",
        )

        self.user2 = Profile.objects.create(
            name="Anderson Silva",
            short_name="Anderson",
            default_download_format="mp_320",
            keyword="asilva",
        )

    def test_fan_mail(self):
        fan_mail = Message.objects.create(
            from_profile=self.user1, to_profile=self.user2
        )

        feed = Feed.notify_fan_mail(
            from_profile=self.user1, to_profile=self.user2, item=fan_mail
        )

        self.assertEqual(feed.feed_type, "fan_mail")
        self.assertEqual(feed.from_profile, self.user1)
        self.assertEqual(feed.to_profile, self.user2)
        self.assertEqual(feed.item, fan_mail)

    def test_review(self):
        review = Review.objects.create(
            review="Something", profile=self.user1, reviewer=self.user2
        )

        feed = Feed.notify_review(
            from_profile=self.user1, to_profile=self.user2, item=review
        )

        self.assertEqual(feed.feed_type, "review")
        self.assertEqual(feed.item, review)

    def test_tip(self):
        # pending: no current tip action
        pass

    def test_fan_user(self):
        fan = Fan.objects.create(fanee=self.user1, faner=self.user2)

        feed = Feed.notify_fan_user(
            from_profile=self.user1, to_profile=self.user2, item=fan
        )

        self.assertEqual(feed.feed_type, "fan_user")
        self.assertEqual(feed.item, fan)

    def test_fan_song(self):
        song = Song.objects.create(profile=self.user2, title="Angel")

        song_fan_event = SongFanEvent.objects.create(faned_song=song, faner=self.user2)

        feed = Feed.notify_fan_song(
            from_profile=self.user1, to_profile=self.user2, item=song_fan_event
        )

        self.assertEqual(feed.feed_type, "fan_song")
        self.assertEqual(feed.item, song_fan_event)

    def test_fan_album(self):
        album = Album.objects.create(profile=self.user2, title="Collection")

        album_fan_event = AlbumFanEvent.objects.create(
            faned_album=album, faner=self.user1
        )

        feed = Feed.notify_fan_album(
            from_profile=self.user1, to_profile=self.user2, item=album_fan_event
        )

        self.assertEqual(feed.feed_type, "fan_album")
        self.assertEqual(feed.item, album_fan_event)

    def test_played_song(self):
        # song belongs to user2 and user1 played it

        song = Song.objects.create(profile=self.user2, title="Angel")

        played_song = Play.objects.create(player=self.user1, played_song=song)

        feed = Feed.notify_played_song(
            from_profile=self.user1, to_profile=self.user2, item=played_song
        )

        self.assertEqual(feed.feed_type, "played_song")
        self.assertEqual(feed.item, played_song)

    def test_new_event(self):
        event = Event.objects.create(
            profile=self.user2,
            title="Silva Concert",
            starts=datetime.datetime(2011, 10, 1, 20, 00),
            ends=datetime.datetime(2011, 10, 2, 00, 00),
        )

        feed = Feed.notify_new_event(
            from_profile=self.user1, to_profile=self.user2, item=event
        )

        self.assertEqual(feed.feed_type, "new_event")
        self.assertEqual(feed.item, event)
