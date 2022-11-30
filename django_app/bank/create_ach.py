import django

django.setup()

from payment_processing.views import create_ach


create_ach()
