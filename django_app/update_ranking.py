import datetime

import django

django.setup()

from accounts.models import Profile
from media.models import Song, Album
import ranking
from django.db.models import Count

import logging

logger = logging.getLogger("email_notifications")


def update_all():
    """
    When we run this file as a script, update all the Profile, Song, and Album
    objects.

    Measure the execution time under t0.
    """

    t0 = datetime.datetime.now()

    """ For directory ranking """
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
    albums = Album.objects.all()

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

    logger.info("Logging successful ranking update completed in %s seconds.", runtime)

    logger.info("update_rankings runtime %s seconds", runtime)

    logger.info("Done.")


if __name__ == "__main__":
    update_all()
