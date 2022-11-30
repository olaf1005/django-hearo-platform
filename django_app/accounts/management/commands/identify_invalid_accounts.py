"Run example ./manage.py identify_invalid_accounts --date=8/1/2021 --validator=quickemailverification --limit=10 --check-token-balance --test=(optional single email to test)"
import logging
import datetime
from django.core.exceptions import ValidationError
import requests
import json
import csv
import dateutil.parser as parser

from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings

from accounts.models import Profile

import hedera_utils

from django.core.exceptions import ValidationError
from disposable_email_checker.validators import validate_disposable_email

import quickemailverification


logger = logging.getLogger(__name__)

ONE_MONTH_AGO = datetime.date.today() - datetime.timedelta(days=30)

SENDGRID_VALIDATIONS_URL = "https://api.sendgrid.com/v3/validations/email"

SENDGRID_EMAIL_VALIDATION_HEADERS = {
    "authorization": "Bearer {}".format(settings.SENDGRID_EMAIL_VALIDATION_API_KEY),
    "content-type": "application/json",
}


class Command(BaseCommand):
    help = "Identifies and invalidates compromised or inauthentic accountsChecks token balances for all accounts after a date"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--date",
            type=str,
            help="Date from which to check for invalid accounts",
            default=ONE_MONTH_AGO.strftime("%Y-%m-%d"),
        )
        parser.add_argument(
            "--test", type=str, help="Single email to test", default=None,
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Set a limit to the number of emails to check",
            default=-1,
        )
        parser.add_argument(
            "--check-token-balance",
            dest="check_token_balance",
            help="Checks and updates token balance and adds it to the CSV",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--validator",
            type=str,
            help="Which validator to use",
            choices=["sendgrid", "quickemailverification", "disposable_email_checker"],
            default="disposable_email_checker",
        )

    # Validation methods
    def sendgrid_validation_request(self, data):
        result = requests.post(
            SENDGRID_VALIDATIONS_URL,
            data=json.dumps(data),
            headers=SENDGRID_EMAIL_VALIDATION_HEADERS,
        ).json()
        logger.info(result)
        return result["result"]["verdict"] == "Valid"

    def quickemailverification_validation_request(self, data):
        client = quickemailverification.Client(
            settings.QUICKEMAILVERIFICATION_API_KEY
        ).quickemailverification()
        response = client.verify(data["email"])
        logger.info(response.body)
        if (
            response.body["result"] == "valid"
            and response.body["disposable"] == "false"
            and response.body["safe_to_send"] == "true"
        ):
            return True
        return False

    def disposable_email_checker_validation_request(self, data):
        try:
            validate_disposable_email(data["email"])
            return True
        except ValidationError:
            return False

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

    def handle(self, *args, **options):
        date_from_which_to_check = parser.parse(options["date"])
        test = options["test"]
        validator = options["validator"]
        limit = options["limit"]
        check_token_balance = options["check_token_balance"]

        if validator == "sendgrid":
            validation_method = self.sendgrid_validation_request
        elif validator == "quickemailverification":
            validation_method = self.quickemailverification_validation_request
        elif validator == "disposable_email_checker":
            validation_method = self.disposable_email_checker_validation_request
        else:
            validation_method = self.disposable_email_checker_validation_request

        if test:
            profiles = Profile.objects.filter(user__email=test)
        else:
            profiles = Profile.objects.filter(
                date_added__gte=date_from_which_to_check,
                deactivated=False,
                user__is_active=True,
            ).order_by("date_added")

        balances = []

        logger.info("{} ACCOUNTS TO CHECK".format(profiles.count()))

        try:

            for profile in profiles:
                try:
                    if limit == 0:
                        break

                    limit -= 1

                    user = profile.user

                    data = {"email": user.email, "source": "signup"}

                    is_valid = validation_method(data)

                    balance = 0

                    if not is_valid:
                        logger.info("{} NOT VALID".format(data["email"]))
                        if check_token_balance:
                            try:
                                balance = hedera_utils.check_token_balance_on_hedera_network(
                                    user
                                )
                                logger.info("userbalance {}".format(balance))
                                wallet = user.wallet
                                wallet.token_balance = balance
                                wallet.save()
                            except Exception:
                                pass
                    else:
                        logger.info("{} VALID".format(data["email"]))

                    balance_stuff = {
                        "user_id": user.id,
                        "date_added": str(profile.date_added),
                        "user_email": user.email,
                        "status": "VALID" if is_valid else "INVALID",
                        "balance": balance,
                    }
                    balances.append(balance_stuff)
                except Exception:
                    pass
        except Exception:
            pass

        self.write_csv(
            "identify_and_deactivate_balances_for_users",
            date_from_which_to_check,
            balances,
        )

        logger.info("Identified {} invalid emails".format(len(balances)))

        logger.info("Done.")
