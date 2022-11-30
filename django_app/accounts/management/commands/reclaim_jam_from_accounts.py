"""
Run ./manage.py reclaim_jam_from_accounts --csv-file=file.csv --transfer-to-hedera-account=account_id

Goes through a csv file in the format

user_id | email

and checks each user balance. If the balance is greater than 0,  it checks to
see if the user has a recovery key.

If a recovery key is found, it unlocks the recovery key to create a new
transaction after passwords for at least 2 recovery keys have been requested
through a passport prompt and entered into the command line without echoing.

The transaction transfers the amount to the account id specified by --transfer-to.

"""
import logging
import datetime
import getpass
import csv
import dateutil.parser as parser
from django.contrib.auth.models import User

from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings

from accounts.models import Profile

import hedera_utils

import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reclaims JAM from accounts specified in a CSV file using the minimum set of keys required to recover a key used to reclaim the JAM"

    passwords = []

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--csv-file",
            type=str,
            help="CSV file to process in the format of user_id | email (Email is used for reference purposes only)",
        )
        parser.add_argument(
            "--transfer-to-hedera-account",
            type=str,
            help="Hedera Account ID to transfer to",
        )

        parser.add_argument(
            "--test",
            dest="test",
            help="Just outputs the number of accounts the script will process",
            default=False,
            action="store_true",
        )

    def write_csv(self, fname, date, dict_data):
        csv_file = "{fname}_{date}.csv".format(
            fname=fname, date=date.strftime("%Y-%m-%d")
        )
        try:
            with open(csv_file, "w") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=[
                        "user_id",
                        "date_added",
                        "user_email",
                        "status",
                        "balance",
                    ],
                )
                writer.writeheader()
                for data in dict_data:
                    writer.writerow(data)
            logger.info("Wrote csv file {}".format(csv_file))
        except IOError:
            print("I/O error")

    def get_recovery_users_and_passes(self, user):
        for i in range(0, settings.NUM_AUTHORIZERS_REQUIRED_FOR_PASSWORD_RESET - 1):
            logger.info("Requesting password for authorizer #{}".format(i))
            try:
                password = getpass.getpass()
                self.passwords.append(password)
            except Exception as error:
                logger.error("ERROR", error)

    def transfer_funds_to_treasury(self, user):
        tokentransfer = HTSTokenTransfer(
            listen=listen,
            from_user=request.user,
            for_song=song,
            value=value,
            facilitation_fee=facilitation_fee,
            data=data,
        )
        tokentransfer.save()
        tokentransfer.transfer_token(private_key)

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        test = options["test"]
        transfer_to_account_id_ = options["transfer-to-hedera-account"]
        total = 0
        reclaimed_accounts = []

        with open(csv_file) as file:
            data = {values[0]: values[1:] for values in zip(*csv.reader(file))}

        users = User.objects.filter(pk__in=data["user_id"])

        if test:
            logger.info("{} profiles to process".format(users.count()))
        else:

            for user in users:
                token_balance = hedera_utils.check_token_balance_on_hedera_network(user)
                if token_balance > 0:
                    total += self.transfer_funds_to_treasury(user, token_balance)
                    reclaimed_accounts.append(
                        dict(email=user.email, balance=token_balance)
                    )

        self.write_csv(
            "identify_and_deactivate_balances_for_users",
            datetime.date.today(),
            reclaimed_accounts,
        )

        logger.info(
            "Reclaimed {} accounts for a total value of {}".format(
                len(reclaimed_accounts, total)
            )
        )

        logger.info("Done.")
