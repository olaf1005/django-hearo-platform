# -*- coding: utf-8 -*-
"""
Should be called like this:

./manage.py bulk_import --catalog catalog.csv --directory ./rnb/rnb/ --userid 4143 --genre Rnb
"""
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from utils import sendemail_template


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send an email to a user or all users"

    option_list = BaseCommand.option_list + (
        make_option("--email", action="store", dest="userid", help="Email address"),
        make_option(
            "--all", action="store", dest="directory", help="Send to all users"
        ),
        make_option("--template", action="store", dest="catalog", help="The template"),
    )

    def handle(self, *args, **options):
        email = options.get("email")
        all = options.get("true")
        template = options.get("template")
        if email:
            sendemail_template([email], template, {})
        elif all:
            emails = [email[0] for email in User.objects.all().values_list("email")]
            sendemail_template(email, template, {})
