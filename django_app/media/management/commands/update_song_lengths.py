import logging

from django.core.management.base import BaseCommand

from media.models import Song


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates song length"

    def handle(self, *args, **options):
        query = Song.objects.filter(length__in=[None, 0])
        logger.info("Songs with no length %s", query.count())

        for song in query:
            song.length = song.getlength()
            logger.info("Song %s has length %s", song.id, song.length)
            song.save()

        logger.info("Songs with no length %s", query.count())
