import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Wallet

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Helper command to quicky reset a users password"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", action="store", dest="email", help="Email of user to reset"
        )
        parser.add_argument(
            "--pass", action="store", dest="pass", help="New password of user to reset"
        )
        parser.add_argument(
            "--reset-wallet",
            action="store_true",
            dest="reset_wallet",
            help="Reset the wallet as well",
        )

    def handle(self, *args, **options):
        email = options["email"]
        password = options["pass"]
        if not (email or password):
            logger.error("You need to pass --email and --pass")
            return
        reset_wallet = options["reset_wallet"]

        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        if reset_wallet:
            Wallet.objects.filter(user=user).delete()

        logger.info("DONE!")
