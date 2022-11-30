import django

django.setup()

from django.conf import settings


from email_from_template import send_mail


send_mail(
    ("me@artur.co",),
    "email_announcements/06072013.html",
    {},
    "notifications@{}".format(settings.BASE_URL),
)
