import logging
import datetime

from django.db.models import Count
from django.core.management.base import BaseCommand

from accounts.models import Profile
from media.models import Song, Album

from . import update_ranking


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates the hotness or ranking for profiles"

    def handle(self, *args, **options):
        update_ranking.update_all()
