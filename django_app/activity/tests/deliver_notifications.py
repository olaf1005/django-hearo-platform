# from django.test import TestCase
from .support.hearo_test_case import HearoTestCase
from django.core import mail

from accounts.models import Profile
from accounts.models import Organization, Band
from activity.models import Feed
from django.conf import settings


import unittest


class DeferredNotificationsTest(HearoTestCase):
    def setUp(self):
        self.profile1 = self.createProfile1(
            self.createSettings(notify_fan=True, notify_fan_threshold=5)
        )
        self.profile2 = self.createProfile2()
        self.profile3 = self.createUserProfile(
            "Peter",
            "Peter Weickman",
            "peter",
            "peter@aol.com",
            self.createSettings(notify_fan=True, notify_fan_threshold=5),
        )
        self.profile4 = self.createUserProfile(
            "Fernando",
            "Fernando Passaro",
            "passarinho",
            "passarinho@globo.com",
            self.createSettings(notify_fan=True, notify_fan_threshold=5),
        )
        self.profile5 = self.createUserProfile(
            "John",
            "John Estrada",
            "jestrada",
            "jestrada@gmail.com",
            self.createSettings(notify_fan=True, notify_fan_threshold=5),
        )
        self.profile6 = self.createUserProfile(
            "Paul",
            "Paul Pfeifer",
            "ppfeifer",
            "paul.pfeifer@hotmail.com",
            self.createSettings(notify_fan=True, notify_fan_threshold=5),
        )

    def createNotifications(self, create_fifth=False):
        self.createFan(self.profile1, self.profile2)
        self.createFan(self.profile3, self.profile2)
        self.createFan(self.profile4, self.profile2)
        self.createFan(self.profile5, self.profile2)

        if create_fifth:
            self.createFan(self.profile6, self.profile2)

    def test_before_minimum_limit(self):
        self.createNotifications(False)
        self.deliver_notifications.start()

        self.assertEqual(len(mail.outbox), 0)

    def test_after_minimum_limit(self):
        self.createNotifications(True)
        self.deliver_notifications.start()

        self.assertEqual(len(mail.outbox), 1)

    def test_feed_items(self):
        self.createNotifications(True)
        self.deliver_notifications.start()

        body = mail.outbox[0].body

        self.assertContainsStr(
            body,
            '<a href="https://{}/profile/fcoury">Felipe Coury</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(
            body,
            '<a href="https://{}/profile/peter">Peter Weickman</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(
            body,
            '<a href="https://{}/profile/passarinho">Fernando Passaro</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(
            body,
            '<a href="https://{}/profile/jestrada">John Estrada</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(
            body,
            '<a href="https://{}/profile/ppfeifer">Paul Pfeifer</a>'.format(
                settings.BASE_URL
            ),
        )


class DisabledSettingTest(HearoTestCase):
    def setUp(self):
        profile1 = self.createProfile1()
        profile2 = self.createProfile2(
            self.createSettings(notify_fan=False, notify_fan_threshold=0)
        )

        self.feed = self.createNotifyFanUser(
            profile1, profile2, self.createFan(profile1, profile2)
        )

    def test_feed_is_not_sent(self):
        self.assertEqual(len(mail.outbox), 0)

    def test_feed_is_marked_as_delivered(self):
        self.feed = Feed.objects.get(pk=self.feed.pk)
        self.assertIsNotNone(self.feed.delivered_at)


class InvalidProfileTest(HearoTestCase):
    def setUp(self):
        profile1 = self.createProfile1()
        profile2 = self.createProfile("Felipe", "Felipe", None)

        feed = self.createNotifyReview(
            profile1, profile2, self.createReview(profile1, profile2)
        )


class MultipleSingleFeeds(HearoTestCase):
    def setUp(self):
        profile1 = self.createProfile1()
        profile2 = self.createProfile2()

        self.createReview(profile1, profile2)
        self.createReview(profile1, profile2)
        self.createReview(profile1, profile2)
        self.createReview(profile1, profile2)
        self.createReview(profile1, profile2)


class DeliverNotificationsTest(HearoTestCase):
    def setUp(self):
        profile1 = self.createProfile1()  # felipe
        profile2 = self.createProfile2(self.createSettingsWithZero())  # anderson

        fan_mail = self.createFanMail(profile1, profile2)
        review = self.createReview(profile1, profile2)
        fan = self.createFan(profile1, profile2)
        song = self.createSong(profile2, "Angel")
        album = self.createAlbum(profile2)
        radio = self.createRadio(profile2)

        song_fan_event = self.createSongFanEvent(profile1, song)
        album_fan_event = self.createAlbumFanEvent(profile1, album)

        played_song = self.createPlayedSong(profile1, song)
        played_album = self.createPlayedAlbum(profile1, album, song)
        played_radio = self.createPlayedRadio(profile1, radio, song)

        new_event = self.createEvent(profile2, "Silva Concert")

        status_update = self.createStatusUpdate(profile2, "I am crazy")

    def test_mark_as_delivered(self):
        # load the feeds
        feeds0 = Feed.objects.get(pk=1)
        feeds1 = Feed.objects.get(pk=2)

        # assure they have been given a delivered at date
        self.assertIsNotNone(feeds0.delivered_at)
        self.assertIsNotNone(feeds1.delivered_at)

    def test_fan_mail_email(self):
        msg = mail.outbox[0]

        self.assertEqual(msg.subject, "You have a new message")

        self.assertContainsStr(msg.body, "Hi Anderson")
        self.assertContainsStr(msg.body, "I am just crazy for your new album!")
        self.assertContainsStr(msg.body, "I can&#39;t explain how much I love it...")

        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/mail/view?messageid=1">I am just crazy for your new album!</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/mail/view?messageid=1">Click here</a>'.format(
                settings.BASE_URL
            ),
        )

    def test_review_email(self):
        msg = mail.outbox[1]

        self.assertEqual(msg.subject, "Someone just reviewed you!")

        self.assertContainsStr(msg.body, "Hi Anderson")
        self.assertContainsStr(msg.body, "Best indy R&amp;B guy around")

    @unittest.skip("tipping isn't implemented yet")
    def test_tip_email(self):
        pass

    def test_fan_user_email(self):
        msg = mail.outbox[2]

        self.assertEqual(msg.subject, "You have new fans!")

        self.assertContainsStr(msg.body, "Hi Anderson")
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/profile/fcoury">Felipe Coury</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(msg.body, "has fanned your profile")

    def test_fan_song_email(self):
        msg = mail.outbox[2]

        self.assertContainsStr(msg.body, "Hi Anderson")
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/profile/fcoury">Felipe Coury</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(msg.body, "has fanned your song Angel")

    def test_fan_album_email(self):
        msg = mail.outbox[2]

        self.assertContainsStr(msg.body, "Hi Anderson")
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/profile/fcoury">Felipe Coury</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(msg.body, "has fanned your album The Album")

    def test_played_song_email(self):
        msg = mail.outbox[3]

        self.assertEqual(msg.subject, "Your music was recently played")

        self.assertContainsStr(msg.body, "Hi Anderson")
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/profile/fcoury">Felipe Coury</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(msg.body, "played your song Angel")

    def test_played_album_email(self):
        msg = mail.outbox[3]

        self.assertContainsStr(msg.body, "Hi Anderson")
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/profile/fcoury">Felipe Coury</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(msg.body, "played your album The Album")

    def test_played_radio_email(self):
        msg = mail.outbox[3]

        self.assertContainsStr(msg.body, "Hi Anderson")
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/profile/fcoury">Felipe Coury</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(msg.body, "played your radio")

    def test_new_event_email(self):
        msg = mail.outbox[4]

        self.assertEqual(
            msg.subject, "A new event you might be interested in was just posted"
        )

        self.assertContainsStr(msg.body, "Hi Felipe")
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/profile/asilva">Anderson Silva</a>'.format(
                settings.BASE_URL
            ),
        )
        self.assertContainsStr(msg.body, "has just created a new event")
        self.assertContainsStr(
            msg.body,
            '<a href="https://{}/events/1">Silva Concert</a>'.format(settings.BASE_URL),
        )


class BandSingleNotificationTest(HearoTestCase):
    def setUp(self):
        self.profile1 = self.createProfile1()  # felipe
        self.profile2 = self.createProfile2()
        self.band_profile = Profile.objects.create(
            name="The Band",
            short_name="TheBand",
            keyword="the_band",
            default_download_format="mp3_320",
            settings=self.createSettings(notify_fan_threshold=0),
        )

        self.organization = Organization.objects.create(
            profile=self.band_profile, is_band=True, band=Band.objects.create()
        )

        self.organization.add_member(self.profile2.person)

        self.fan_mail = self.createFanMail(self.profile1, self.band_profile)

    def test_new_fanmail_email(self):
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertEqual(msg.subject, "You have a new message")
        self.assertContainsStr(msg.body, "Hi TheBand")


class BandMultiNotificationTest(HearoTestCase):
    def setUp(self):
        self.profile1 = self.createProfile1()  # felipe
        self.profile2 = self.createProfile2()
        self.profile3 = self.createProfile3()

        self.band_profile = Profile.objects.create(
            name="The Band",
            short_name="TheBand",
            keyword="the_band",
            default_download_format="mp3_320",
        )

        self.organization = Organization.objects.create(
            profile=self.band_profile, is_band=True, band=Band.objects.create()
        )

        self.organization.add_member(self.profile2.person)
        self.organization.add_member(self.profile3.person)

        self.feed = self.createNotifyFanUser(
            self.profile1,
            self.band_profile,
            self.createFan(self.profile1, self.band_profile),
        )
        self.feed = self.createNotifyFanUser(
            self.profile1,
            self.band_profile,
            self.createFan(self.profile1, self.band_profile),
        )
        self.feed = self.createNotifyFanUser(
            self.profile1,
            self.band_profile,
            self.createFan(self.profile1, self.band_profile),
        )
        self.feed = self.createNotifyFanUser(
            self.profile1,
            self.band_profile,
            self.createFan(self.profile1, self.band_profile),
        )
        self.feed = self.createNotifyFanUser(
            self.profile1,
            self.band_profile,
            self.createFan(self.profile1, self.band_profile),
        )

    def test_number_of_emails_sent(self):
        self.assertEqual(len(mail.outbox), 2)

    def test_first_message(self):
        msg = mail.outbox[0]

        self.assertEqual(msg.subject, "You have new fans!")
        self.assertContainsStr(msg.body, "Hi TheBand")

        self.assertEqual(msg.recipients(), [self.profile2.user.email])

    def test_second_message(self):
        msg = mail.outbox[1]

        self.assertEqual(msg.subject, "You have new fans!")
        self.assertContainsStr(msg.body, "Hi TheBand")

        self.assertEqual(msg.recipients(), [self.profile3.user.email])
