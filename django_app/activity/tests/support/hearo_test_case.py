from django.test import TestCase

from accounts.models import (
    Fan,
    Profile,
    Settings,
    Review,
    AlbumFanEvent,
    SongFanEvent,
    Person,
    StatusUpdate,
)
from activity.models import Feed
from events.models import Event
from mail.models import Message
from media.models import Album, Song, Radio
from player.models import Play

from django.contrib.auth.models import User

import datetime


class HearoTestCase(TestCase):
    def assertContainsStr(self, string, match):
        assert match in string, 'string "%s" doesn\'t contain "%s"' % (string, match)

    def createUser(self, email):
        return User.objects.create(username=email, email=email)

    def createSettings(self, **fields):
        return Settings.objects.create(**fields)

    def createProfile(self, short_name, name, user, settings=None):
        username = user.username if user else ""
        profile = Profile.objects.create(
            name=name,
            short_name=short_name,
            default_download_format="mp_320",
            keyword=username,
            user=user,
        )
        if user:
            person = Person.objects.create(user=user, profile=profile, view=profile)

        if settings:
            profile.settings = settings
            profile.save()
        return profile

    def createUserProfile(self, short_name, name, email, settings=None):
        user = self.createUser(email)
        return self.createProfile(short_name, name, user, settings)

    def createFanMail(self, from_profile, to_profile):
        return Message.objects.create(
            from_profile=from_profile,
            to_profile=to_profile,
            subject="I am just crazy for your new album!",
            body="I can't explain how much I love it...",
        )

    def createReview(self, reviewer, profile):
        return Review.objects.create(
            review="Best indy R&B guy around", profile=profile, reviewer=reviewer
        )

    def createFan(self, faner, fanee):
        return Fan.objects.create(faner=faner, fanee=fanee)

    def createSong(self, profile, title="Song"):
        return Song.objects.create(profile=profile, title=title)

    def createSongFanEvent(self, profile, song):
        return SongFanEvent.objects.create(faner=profile, faned_song=song)

    def createAlbum(self, profile, title="The Album"):
        return Album.objects.create(profile=profile, title=title)

    def createAlbumFanEvent(self, profile, album):
        return AlbumFanEvent.objects.create(faner=profile, faned_album=album)

    def createRadio(self, profile):
        return Radio.objects.create(profile=profile)

    def createPlayedSong(self, player, song):
        return Play.objects.create(player=player, played_song=song)

    def createPlayedAlbum(self, player, album, song):
        return Play.objects.create(player=player, album=album, played_song=song)

    def createPlayedRadio(self, player, radio, song):
        return Play.objects.create(player=player, radio=radio, played_song=song)

    def createEvent(self, profile, title="The Event"):
        event = Event.objects.create(
            profile=profile,
            title="Silva Concert",
            starts=datetime.datetime(2011, 10, 1, 20, 00),
            ends=datetime.datetime(2011, 10, 2, 00, 00),
        )
        event.artists.add(profile)
        event.save()

        return event

    def createStatusUpdate(self, profile, status):
        StatusUpdate.objects.create(profile=profile, status=status)

    def createNotifyFanMail(self, profile1, profile2, fan_mail):
        return Feed.notify_fan_mail(
            from_profile=profile1, to_profile=profile2, item=fan_mail
        )

    def createNotifyReview(self, profile1, profile2, review):
        return Feed.notify_review(
            from_profile=profile1, to_profile=profile2, item=review
        )

    def createNotifyFanUser(self, profile1, profile2, fan):
        return Feed.notify_fan_user(
            from_profile=profile1, to_profile=profile2, item=fan
        )

    def createNotifyFanSong(self, profile1, profile2, song_fan_event):
        return Feed.notify_fan_song(
            from_profile=profile1, to_profile=profile2, item=song_fan_event
        )

    def createNotifyFanAlbum(self, profile1, profile2, album_fan_event):
        return Feed.notify_fan_album(
            from_profile=profile1, to_profile=profile2, item=album_fan_event
        )

    def createNotifyPlayedSong(self, profile1, profile2, played_song):
        return Feed.notify_played_song(
            from_profile=profile1, to_profile=profile2, item=played_song
        )

    def createNotifyPlayedAlbum(self, profile1, profile2, played_album):
        return Feed.notify_played_album(
            from_profile=profile1, to_profile=profile2, item=played_album
        )

    def createNotifyPlayedRadio(self, profile1, profile2, played_radio):
        return Feed.notify_played_radio(
            from_profile=profile1, to_profile=profile2, item=played_radio
        )

    def createNotifyNewEvent(self, profile1, profile2, new_event):
        return Feed.notify_new_event(
            from_profile=profile1, to_profile=profile2, item=new_event
        )

    def createUser1(self):
        return self.createUser("felipe@coury.com.br")

    def createUser2(self):
        return self.createUser("anderson@silva.com.br")

    def createUser3(self):
        return self.createUser("peter@ghostbusters.com")

    def createProfile1(self, settings=None):
        return self.createProfile(
            "Felipe", "Felipe Coury", self.createUser1(), settings
        )

    def createProfile2(self, settings=None):
        return self.createProfile(
            "Anderson", "Anderson Silva", self.createUser2(), settings
        )

    def createProfile3(self, settings=None):
        return self.createProfile(
            "Peter", "Peter Weickmann", self.createUser3(), settings
        )

    def createSettingsWithZero(self):
        return self.createSettings(
            notify_fan=True,
            notify_fan_threshold=0,
            notify_play=True,
            notify_play_threshold=0,
        )
