from django.core.management.base import BaseCommand
from payment_processing.views import create_ach_transmittal_record


class Command(BaseCommand):
    def handle(self, *args, **options):
        create_ach_transmittal_record()
