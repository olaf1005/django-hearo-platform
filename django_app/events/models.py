from django.db import models
from django.db.models.signals import post_save

from activity.models import Feed

import datetime


class FanEvent(models.Model):
    fanner = models.ForeignKey(
        "accounts.Profile", related_name="fan_events", on_delete=models.CASCADE
    )
    fanned_event = models.ForeignKey(
        "Event", related_name="fan_events", on_delete=models.CASCADE
    )
    fanned_date = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        get_latest_by = "fanned_date"


class Event(models.Model):
    profile = models.ForeignKey(
        "accounts.Profile", related_name="events", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=60)
    starts = models.DateTimeField()
    ends = models.DateTimeField(null=True, blank=True)
    venue = models.ForeignKey(
        "accounts.Venue", null=True, blank=True, on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        "accounts.Location", null=True, blank=True, on_delete=models.SET_NULL
    )
    location_text = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    ticket_url = models.CharField(blank=True, max_length=300)
    artists = models.ManyToManyField(
        "accounts.Profile", blank=True, related_name="shows"
    )

    class Meta:
        get_latest_by = "created"

    def add_fan(self, profile):
        f, created = FanEvent.objects.get_or_create(fanned_event=self, fanner=profile)
        return created

    def remove_fan(self, profile):
        if FanEvent.objects.filter(fanned_event=self, fanner=profile).exists():
            FanEvent.objects.get(fanned_event=self, fanner=profile).delete()
            # wtf??? this is in all others
            return ",'>)"
        return None

    def jsonify(self, request):
        mine = fanned = logged_in = 0
        if request.user.is_authenticated:
            if request.user.person.view == self.profile:
                mine = 1
            if self.fan_events.filter(fanner=request.user.person.view).exists():
                fanned = 1
            logged_in = 1
        end = self.ends if self.ends else self.starts + datetime.timedelta(hours=1)
        if request.user.is_authenticated:
            view = request.user.person.view
        else:
            # TODO: danielnordberg: unused var Wed Feb 25 17:01:50 EAT 2015
            view = ""
        return {
            "artists": [a.jsonify(request) for a in self.artists.all()],
            "short_month": self.starts.strftime("%b"),
            "day": self.starts.strftime("%d"),
            "mine": mine,
            "title": self.title,
            "profile": self.profile.jsonify(request),
            "location": self.location.most_exact if self.location else "",
            "location_text": self.location_text,
            "description": self.description,
            "id": self.id,
            "s_string": self.starts.strftime("%A, %B %d at %I:%M%p"),
            "e_string": self.ends.strftime("%A, %B %d at %I:%M%p") if self.ends else "",
            "allDay": False,
            "fanned": fanned,
            "start": self.starts.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "logged_in": logged_in,
            "form_starts": self.starts.strftime("%Y-%m-%d %I:%M").strip(),
            "form_ends": self.ends.strftime("%Y-%m-%d %I:%M").strip()
            if self.ends
            else "",
            "ticket_url": self.ticket_url,
        }


def create_feed_for_event(sender, **kwargs):
    event = kwargs["instance"]
    # we only send notification if this event already have
    # artists associated, in a way that we can find all the
    # fans of the artists
    for artist in event.artists.all():
        for fan in artist.get_fans():
            Feed.notify_new_event(from_profile=artist, to_profile=fan, item=event)


post_save.connect(create_feed_for_event, Event)
