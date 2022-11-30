import logging

from activity.models import Feed
from django.core.management.base import BaseCommand
from django.conf import settings

from accounts.models import Profile
from django.contrib.contenttypes.models import ContentType


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Create weekly digest"""

        ct = ContentType.objects.get_for_model(Profile)

        for profile in Profile.objects.filter(settings__receive_weekly_digest=True):
            if (
                profile.get_fans_last_week()
                or profile.get_songfans_last_week()
                or profile.get_albumfans_last_week()
                or profile.get_songuploads_last_week()
                or profile.get_albumuploads_last_week()
                or profile.get_library_newsongsfaned_last_week()
                or profile.get_library_newalbumsfaned_last_week()
                or profile.get_library_newprofilesfaned_last_week()
                or profile.get_downloadcharges_last_week()
            ):
                feed = Feed(
                    feed_type="weekly_digest",
                    from_profile_id=settings.HEARO_TEAM_PROFILE_ID,
                    to_profile=profile,
                    content_type=ct,
                    object_id=profile.id,
                )
                feed.save()
