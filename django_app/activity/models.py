from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import fields
from django.template import loader


FEED_TYPES = [
    ("fan_mail", "Fan Mail"),
    ("review", "Review"),
    ("tip", "Tip"),
    ("fan_user", "Fan User"),
    ("fan_song", "Fan Song"),
    ("fan_album", "Fan Album"),
    # ('fan_event',   'Fan Event') ?
    ("played_song", "Played Song"),
    ("played_album", "Played Album"),
    ("played_radio", "Played Radio"),
    ("new_event", "New Event"),
    ("status_update", "Status Update"),
    ("download_link", "Download Link"),
    ("weekly_digest", "Weekly digest"),
    ("monthly_digest", "Monthly digest"),
    ("yearly_digest", "Yearly digest"),
]


def add_feed_types(cls):
    "creates a notify_[feed_type] method for each feed type"
    for type_tuple in FEED_TYPES:
        kind, name = type_tuple

        def make_notify(kind):
            def notify(self, **kwargs):
                return self.create(kind, **kwargs)

            return notify

        notify = make_notify(kind)
        notify.__name__ = "notify_%s" % kind
        setattr(cls, notify.__name__, classmethod(notify))

    return cls


# The Feed model is the core of the notification engine and it
# can double as an activity feed to be displayed for a given
# item (activity subject), a given profile as the activity
# originator (from_profile), or as the activity target (to_profile)
#
# For example:
#   user1   = Profile.objects.get(...)
#   user2   = Profile.objects.get(...)
#   message = Message.object.create(from_profile=user1, to_profile=user2, ...)
#
#   Feed.create(feed_type='fan_mail', from_profile=user1,
#               to_profile=message.to_profile, item=message)
#
#   In this case, the user1 sent a message to user2.
#   The activity subject is the message,
#   the originator is user1, and the target user is user2.
#
#   When creating the fan_mail notification email, it can use
#   the item to display the body of the fan mail and to create
#   a link to its id, can use from_profile to display who sent
#   the fan mail and to_profile to know who to send the email to.
#
# There is an scheduled offline process that consumes all
# activities that are not currently delivered and sends the
# email to the affected profile (to_profile). When it finishes
# successfully, it then toggles delivered to true
#


@add_feed_types
class Feed(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    feed_type = models.CharField(max_length=25, choices=FEED_TYPES)
    from_profile = models.ForeignKey(
        "accounts.Profile", related_name="+", on_delete=models.CASCADE
    )
    to_profile = models.ForeignKey(
        "accounts.Profile", related_name="+", on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = fields.GenericForeignKey("content_type", "object_id")
    delivered_at = models.DateTimeField(null=True)

    # if any model wants to add a reverse relation
    # to the Feed model, it can be achieved by adding
    # this snippet:
    #
    #   feeds = fields.GenericRelation(Feed)

    def __str__(self):
        return "{} - created: {}, delivered: {}, to: {}".format(
            self.feed_type, self.created_at, self.delivered_at, self.to_profile.keyword
        )

    class Meta:
        get_latest_by = "created_at"

    @classmethod
    def create(cls, kind, **kwargs):
        kwargs["feed_type"] = kind
        return cls.objects.create(**kwargs)

    @classmethod
    def count_fan_feed_for(cls, user):
        fan_of = user.profile.get_faned()
        fan_of_profiles = [f.fanee for f in fan_of]
        return Feed.objects.filter(from_profile__in=fan_of_profiles).count()

    @classmethod
    def fan_feed_for(cls, user, page=1, page_size=25):
        fan_of = user.profile.get_faned()
        fan_of_profiles = [f.fanee for f in fan_of]
        start = (page - 1) * page_size
        finish = start + page_size
        result = (
            Feed.objects.filter(from_profile__in=fan_of_profiles)
            .exclude(
                Q(feed_type="monthly_digest")
                | Q(feed_type="weekly_digest")
                | Q(feed_type="yearly_digest")
            )
            .select_related("to_profile", "from_profile")
            .order_by("-created_at")[start:finish]
        )
        return result

    @classmethod
    def decorated_fan_feed_for(cls, user, request, page=1, page_size=25):
        feeds = Feed.fan_feed_for(user, page, page_size)
        result = [FeedDecorator(request, f) for f in feeds if f.is_public()]
        return result

    @classmethod
    def count_user_feed_for(cls, profile, include_private=False):
        query = Feed.objects.filter(from_profile=profile)
        if not include_private:
            query = query.exclude(feed_type="fan_mail")
        return query.count()

    @classmethod
    def user_feed_for(cls, profile, include_private=False, page=1, page_size=25):
        start = (page - 1) * page_size
        finish = start + page_size
        query = Feed.objects.filter(from_profile=profile)
        if not include_private:
            query = query.exclude(feed_type="fan_mail")
        result = query.order_by("-created_at").select_related(
            "from_profile", "to_profile"
        )[start:finish]
        # Filter for only feeds whose related object still exist
        result = [x for x in result if x.item]
        return result

    @classmethod
    def decorated_user_feed_for(
        cls, profile, request, include_private=False, page=1, page_size=25
    ):
        feeds = Feed.user_feed_for(profile, include_private, page, page_size)
        result = [FeedDecorator(request, f) for f in feeds]
        return result

    def is_public(self):
        return self.feed_type != "fan_mail"


class FeedDecorator:
    "Decorator class"

    def __init__(self, request, target):
        self.__request = request
        self.__target = target

    def __getattr__(self, attribute):
        return getattr(self.__target, attribute)

    def body(self, _type):
        template_name = "feeds/%s/%s.html" % (_type, self.__target.feed_type)
        attributes = {"feed": self}
        return loader.render_to_string(template_name, attributes)

    def fan_body(self):
        return self.body("fan")

    def user_body(self):
        return self.body("user")

    def __profile_link(self, p):
        return "<a class='profile-ajax' href='/profile/{}'>{}</a>".format(
            p.keyword, p.name
        )

    def profile_link(self):
        return self.__profile_link(self.__target.from_profile)

    def target_link(self):
        return self.__profile_link(self.__target.to_profile)

    def review_target(self):
        if hasattr(self.item, "profile") and self.item.profile:
            return self.__profile_link(self.item.profile)
        elif hasattr(self.item, "song") and self.item.song:
            return "song %s" % self.item.song.title
        elif hasattr(self.item, "album") and self.item.album:
            return "album %s" % self.item.album.title

    def song(self):
        if hasattr(self.item, "faned_song"):
            return self.item.faned_song
        elif hasattr(self.item, "played_song"):
            return self.item.played_song
        elif hasattr(self.item, "song"):
            return self.item.song

    def song_title(self):
        song = self.song()
        if song is not None:
            return song.title

    def album(self):
        if hasattr(self.item, "faned_album"):
            return self.item.faned_album
        elif hasattr(self.item, "album"):
            return self.item.album

    def as_music_listing(self):
        target = None

        if hasattr(self.item, "played_song"):
            target = self.item.played_song
        elif hasattr(self.item, "faned_song"):
            target = self.item.faned_song
        elif hasattr(self.item, "faned_album"):
            target = self.item.faned_album
        elif hasattr(self.item, "song"):
            target = self.item.song
        elif hasattr(self.item, "album"):
            target = self.item.album

        if target:
            return target.as_music_listing(self.__request)

        return ""
