# -*- coding: utf-8 -*-
"""
Sends verification emails for unverified users between two dates
"""
import logging
import datetime
from dateutil import parser

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from optparse import make_option

from accounts.views import send_verification

from django.test.client import RequestFactory


logger = logging.getLogger(__name__)


def send_verification_emails(user):
    factory = RequestFactory()
    data = dict(email=user.email,)
    request = factory.post("/send-verification/", data)
    request.user = user

    response = send_verification(request)

    if response.content == "t":
        logger.info("Send verification to %s", user.email)
    else:
        logger.warn("Failed to send verification to %s", user.email)


class Command(BaseCommand):
    help = "Sends verification emails to users not currently verified between two dates"

    option_list = BaseCommand.option_list + (
        make_option(
            "--start-date", action="store", dest="start_date", help="Start date"
        ),
        make_option("--end-date", action="store", dest="end_date", help="End date"),
        make_option(
            "--test",
            action="store_true",
            dest="test",
            help="Just calculate the number of users affected",
        ),
        make_option(
            "--email",
            action="store",
            dest="email",
            help="Just perform the action for a single user with email",
        ),
    )

    def handle(self, *args, **options):
        d1 = options.get("start_date")
        if d1:
            d1 = parser.parse(d1)
        d2 = options.get("end_date")
        if d2:
            d2 = parser.parse(d2)
        test = options.get("test")
        email = options.get("email")

        if email:
            user = User.objects.get(email=email)
            d1 = datetime.date(2014, 1, 1)
            d1 = datetime.date(2030, 1, 1)
            if test:
                logger.info("Sending verification to one user %s", email)
            else:
                send_verification_emails(user)
        else:
            query = User.objects.filter(
                person__verified=False, date_joined__gte=d1, date_joined__lte=d2
            )
            logger.info("Sending verification emails to %s users", query.count())
            for user in query:
                if test:
                    logger.info("Sending verification to one user %s", user.email)
                else:
                    send_verification_emails(user)
