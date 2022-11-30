"Run example ./manage.py check_token_balances --date=8/1/2021"
import logging
import datetime

from django.db.models import Count
from django.core.management.base import BaseCommand, CommandError, CommandParser
from optparse import make_option
import dateutil.parser as parser

from accounts.models import Profile, Wallet
from media.models import Song, Album

import ranking
import hedera_utils
import csv


logger = logging.getLogger(__name__)

ONE_MONTH_AGO = datetime.date.today() - datetime.timedelta(days=30)


class Command(BaseCommand):
    help = "Checks token balances for all accounts after a date"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--date",
            type=str,
            help="Date from which to check balances",
            default=ONE_MONTH_AGO.strftime("%Y-%m-%d"),
        )

    def write_csv(self, fname, date, dict_data):
        csv_file = "{fname}_{date}.csv".format(
            fname=fname, date=date.strftime("%Y-%m-%d")
        )
        try:
            with open(csv_file, "w") as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=["user_id", "user_email", "balance"]
                )
                writer.writeheader()
                for data in dict_data:
                    writer.writerow(data)
            logger.info("Wrote csv file {}".format(csv_file))
        except IOError:
            print("I/O error")

    def handle(self, *args, **options):
        date_from_which_to_check = parser.parse(options["date"])
        wallets = Wallet.objects.filter(date_added__gte=date_from_which_to_check)

        balances = []

        for wallet in wallets:
            balance = hedera_utils.check_token_balance_on_hedera_network(wallet.user)
            wallet.token_balance = balance
            balance_stuff = {
                "user_id": wallet.user.id,
                "user_email": wallet.user.email,
                "balance": balance,
            }
            balances.append(balance_stuff)
            logger.info("userbalance {}".format(balance_stuff))
            wallet.save()

        self.write_csv(
            "balances_for_users", date_from_which_to_check, balances,
        )

        logger.info("Done.")
