# -*- coding: utf-8 -*-
"""
Creates profiles for users for which registration broke
"""
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from accounts import views as accviews
from accounts.models import Profile

from optparse import make_option


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create the user info for users for which it broke"

    option_list = BaseCommand.option_list + (
        make_option(
            "--email",
            action="store",
            dest="email",
            help="Perform the action for a single user with email",
        ),
        make_option("--acctype", action="store", dest="acctype", help="Account type"),
        make_option("--city", action="store", dest="city", help="City"),
        make_option("--genre", action="store", dest="genre", help="Genre"),
    )

    def handle(self, *args, **options):
        email = options.get("email")
        acctype = options.get("acctype")
        city = options.get("city")
        genre = options.get("genre")

        if email:
            user = User.objects.get(email=email)
            try:
                profile = user.profile
                logger.error("User already has a profile")
            except Profile.DoesNotExist:
                profile = accviews._create_profile_from_user(user, acctype)
                accviews._update_profile_location(profile, city)
                accviews._update_profile_genre(profile, genre)
                logger.info("Created profile for user %s", user)
