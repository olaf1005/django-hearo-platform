import logging
import datetime

from django.db.models import Count
from django.core.management.base import BaseCommand

from accounts.models import Profile
from media.models import Song, Album

import ranking


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates the hotness or ranking for profiles"

    def handle(self, *args, **options):
        t0 = datetime.datetime.now()

        # For directory ranking
        logger.info("Updating directory metrics. This will take a few minutes.")
        people = Profile.objects.all()
        for prof in people:
            prof.update_dir_rank()

        logger.info("Done with directory ranking.")

        # Only care about artists who will show up on feeds
        artists = Profile.objects.annotate(music_count=Count("music")).filter(
            music_count__gte=1
        )

        # Only care about music by artists who show up on feeds
        songs = Song.objects.filter(deleted=False)
        albums = Album.objects.filter(deleted=False)

        logger.info("Updating music page ranking...")
        logger.info("Artists...%s", artists.count())
        for prof in artists:
            ranking.update(prof)
        logger.info("Songs... %s", songs.count())
        for song in songs:
            ranking.update(song)
        logger.info("Albums...%s", albums.count())
        for album in albums:
            ranking.update(album)

        td = datetime.datetime.now() - t0
        runtime = td.total_seconds()

        logger.info(
            "Logging successful ranking update completed in %s seconds.", runtime
        )

        logger.info("update_rankings %s seconds", runtime)

        logger.info("Done.")
