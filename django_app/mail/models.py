from django.db import models
from django.db.models.signals import post_save

from activity.models import Feed

import datetime


class Message(models.Model):
    from_profile = models.ForeignKey(
        "accounts.Profile",
        related_name="from_messages",
        null=False,
        on_delete=models.CASCADE,
    )
    to_profile = models.ForeignKey(
        "accounts.Profile",
        related_name="to_messages",
        null=False,
        on_delete=models.CASCADE,
    )
    from_deleted = models.BooleanField(default=False)
    to_deleted = models.BooleanField(default=False)
    body = models.TextField(null=False, blank=True)
    timestamp = models.DateTimeField(null=False, auto_now_add=True)
    subject = models.CharField(max_length=100, blank=True)
    read = models.BooleanField(null=False, default=False)

    class Meta:
        get_latest_by = "timestamp"

    def jsonify(self, request):
        now = datetime.datetime.now()
        json = {
            "id": self.pk,
            "from": self.from_profile.jsonify(request),
            "to": self.to_profile.jsonify(request),
            "body": self.body,
            "timestamp": self.timestamp.strftime(
                "%B %d %Y at %I:%M %p"
                if self.timestamp.year != now.year
                else "%B %d at %I:%M %p"
            ),
            "subject": self.subject,
            "read": self.read,
        }
        return json


def create_feed_for_message(sender, **kwargs):
    if kwargs["created"]:
        msg = kwargs["instance"]
        Feed.notify_fan_mail(
            from_profile=msg.from_profile, to_profile=msg.to_profile, item=msg
        )


post_save.connect(create_feed_for_message, Message)
