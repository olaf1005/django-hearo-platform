from django.db import models
from accounts.models import Person


# Create your models here.
OTHER = 0
SITE_DOWNTIME = 1
TARTAR_DOWNTIME = 2
SONG_UPLOADED = 3
DOWNLOAD_READY = 4


class Notice(models.Model):
    message = models.CharField(max_length=200)

    # per PERSON messaging, NOT per PROFILE
    person = models.ForeignKey(Person, related_name="notices")

    # do we need this?
    unread = models.BooleanField(default=True)

    category = models.IntegerField()
