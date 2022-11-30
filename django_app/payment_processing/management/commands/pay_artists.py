import optparse

from django.core.management.base import BaseCommand
from django.db import transaction

from payment_processing.views import create_ach


class Command(BaseCommand):

    args = ""
    help = (
        "Find artists who need to be paid.  Create "
        "receipts for them, then transmit the ACH payments to the bank"
    )

    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "--dryrun",
            action="store_true",
            dest="dryrun",
            default=False,
            help="If supplied, no data will be transmitted to the bank.",
        ),
    )

    def handle(self, *args, **options):

        with transaction.atomic():

            # run create_ach which should now pull receipt objects which
            # state=something and pay them.. set state=batched or whatever
            r = create_ach()

            if r is None:
                return

            if options.get("dryrun"):
                transaction.rollback()
                print("--dryrun provided, no changes committed.")
            else:
                transaction.commit()
                print(r)
