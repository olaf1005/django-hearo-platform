import logging
import datetime
import time
import smtplib

from email_from_template import send_mail

from django.conf import settings
from django.core.management.base import BaseCommand

import settings.utils as setting_utils
from accounts.models import Organization
from activity.models import Feed


logger = logging.getLogger(__name__)


NOTIFICATION_GROUPS = {
    ("fan_mail"): "notify_fan_mail",
    ("review"): "notify_review",
    ("fan_user", "fan_song", "fan_album"): "notify_fan",
    ("played_song", "played_album", "played_radio"): "notify_play",
    ("new_event", "download_link"): "notify_events",
    ("weekly_digest"): "receive_weekly_digest",
    ("monthly_digest"): "receive_monthly_digest",
}

SETTINGS_WITH_THRESHOLD = ("notify_fan", "notify_play")


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Starts delivery of all pending feed entries."""

        self.pending = Feed.objects.filter(delivered_at=None)
        self.to_process = []

        start_time = time.time()
        logger.info(
            "Starting delivery of notifications. %s pending feeds.",
            self.pending.count(),
        )

        feeds_per_user_and_group = {}

        for feed in self.pending:
            group = self.notification_setting_for(feed)
            key = (feed.to_profile, group)
            if key not in feeds_per_user_and_group:
                feeds_per_user_and_group[key] = []
            feeds_per_user_and_group[key].append(feed)

        for feed in self.pending:
            # Get it again to ensure it hasn't already been sent
            feed = Feed.objects.get(pk=feed.pk)

            if feed.delivered_at:
                continue

            group = self.notification_setting_for(feed)
            profile = feed.to_profile
            key = (profile, group)
            total_count = len(feeds_per_user_and_group[key])
            deliver = self.can_deliver(profile, feed)
            minimum = self.threshold_for(profile, feed)

            logger.debug(
                "Key %s is >= %s, got %s - deliver? %s",
                group,
                minimum,
                total_count,
                deliver,
            )

            # -1 says there is no threshold
            if minimum == -1:
                self.process_feed(feed, deliver)
            elif total_count >= minimum:
                if total_count > 1:
                    self.process_multiple_feeds(
                        key, deliver, feeds_per_user_and_group[key]
                    )
                else:
                    self.process_feed(feed, deliver)

        elapsed_time = time.time() - start_time
        logger.info("Finished delivering notifications in %0.2fs", elapsed_time)

    def notification_setting_for(self, feed):
        """
        Retrieves the setting we need to check from a profile Settings
        object to get information about feeds of this type
        """
        for feed_types in list(NOTIFICATION_GROUPS.keys()):
            if feed.feed_type in feed_types:
                setting = NOTIFICATION_GROUPS[feed_types]
                return setting

        return None

    def can_deliver(self, profile, feed):
        """
        Whether or not we can deliver a given feed by
        checking the Settings object for the user profile
        """
        setting = self.notification_setting_for(feed)
        if not setting:
            return True
        return getattr(profile.settings, setting)

    def threshold_for(self, profile, feed):
        """
        Some feed types are only delivered after we accumulated
        a certain number of feeds from the same group of feeds
        (see NOTIFICATION_GROUPS). This method returns what is
        that number (threshold) for a given feed, for a given
        user profile.
        """
        setting = self.notification_setting_for(feed)
        if setting in SETTINGS_WITH_THRESHOLD:
            return getattr(profile.settings, "%s_threshold" % setting)
        return -1

    def determine_emails(self, profile):
        if profile.user:
            return [profile.user.email]
        else:
            try:
                if profile.organization and (
                    profile.organization.is_band or profile.organization.is_venue
                ):
                    return [p.user.email for p in profile.organization.members.all()]
            except Organization.DoesNotExist:
                pass

        return None

    def send(self, to, template_base, attrs):

        template = "{}/email_notifications/{}".format(
            setting_utils.project_path("templates"), template_base
        )

        logger.info("Sending email [%s] to [%s]", template_base, to)

        try:
            send_mail([to], template, attrs, settings.NOTIFICATIONS_EMAIL)
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.exception("Error sending [%s] to [%s]: %s", template_base, to, e)
            return False
        except Exception as e:
            logger.exception("Error sending [%s] to [%s]: %s", template_base, to, e)
            return False

    def process_multiple_feeds(self, group, deliver, feeds):
        """
        Process notification emails for more than one feed of the same time,
        for the same user and for the same feed type.
        """
        mark = True

        if deliver:
            mark = self.send_multiple_notifications(group, feeds)

        if mark:
            [self.mark_as_delivered(feed) for feed in feeds]

    def send_multiple_notifications(self, group, feeds):
        """
        Sends the multiple version of a notification email type. This uses
        a template in the format [group_name]_multiple.html
        """
        emails = self.determine_emails(feeds[0].to_profile)

        if emails:
            result = True

            for email in emails:
                self.send(
                    email,
                    "%s_multiple.html" % group[1],
                    {"profile": feeds[0].to_profile, "feeds": feeds},
                )

            return result
        else:
            logger.info(
                "Couldn't send email to profile %s: no user was associated with it",
                feeds[0].to_profile.keyword,
            )
            return False

    def process_feed(self, feed, deliver):
        """
        Process notification emails for one feed entry.
        """
        mark = True

        if deliver:
            mark = self.send_notification(feed)

        if mark:
            self.mark_as_delivered(feed)

    def send_notification(self, feed):
        """
        Sends the single version of a notification email type. This uses
        a template in the format [feed_type].html
        """
        emails = self.determine_emails(feed.to_profile)

        if emails:
            result = True

            for email in emails:
                self.send(
                    email,
                    "%s.html" % (feed.feed_type),
                    {
                        "profile": feed.to_profile,
                        "from_profile": feed.from_profile,
                        "item": feed.item,
                    },
                )
            return result

        else:
            logger.info(
                "Couldn't send email to profile %s: no user was " "associated with it",
                feed.to_profile.keyword,
            )
            return False

    def mark_as_delivered(self, feed):
        """
        Marks the feed as delivered.
        """
        feed.delivered_at = datetime.datetime.now()
        feed.save()
