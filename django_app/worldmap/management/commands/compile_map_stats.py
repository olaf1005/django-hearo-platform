import logging

from django.core.management.base import BaseCommand

from jawnmower.io import write_json_cache
from accounts.models import Profile

from ...geography import COUNTRIES


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Compiling map stats")

        all_countries = {}
        all_coords = []

        profiles = Profile.objects.all()

        # Get global count
        all_countries["global"] = [profiles.count()]

        for profile in profiles.filter(location_set=True):
            # Traverse all the locations we have registered.
            # Save each unique coordinate pair once,
            # and count how many profiles we have in each country.
            loc = profile.location
            cty = loc.country
            if cty:
                if cty not in all_countries:
                    all_countries[cty] = [1, COUNTRIES[cty]]
                else:
                    all_countries[cty][0] += 1

            # Don't bother showing it if it's just the country name
            if loc.country:
                if loc.secondary != COUNTRIES[loc.country] and loc.secondary:
                    coords = loc.jsonify()
                    coords["count"] = loc.profiles.count()

                    if coords not in all_coords:
                        all_coords.append(coords)

        write_json_cache("map.countries", all_countries)
        write_json_cache("map.coords", all_coords)

        logger.info("Compiled map stats")
