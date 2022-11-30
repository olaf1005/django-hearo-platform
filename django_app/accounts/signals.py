from django.db.models import signals
from django.dispatch import receiver

from accounts.models import Settings, Profile


@receiver(signals.post_save, sender=Profile)
def create_profile_settings(sender, instance, created, **kwargs):
    if not instance.settings:
        instance.settings = Settings.objects.create()
        instance.save()
