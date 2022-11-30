from os import O_NDELAY
from django.db import models
from django.db.models.signals import post_save

from accounts.models import Profile
from media.models import Song, Album, Radio
from activity.models import Feed


class QueuedDownload(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    song = models.ForeignKey(
        Song, related_name="queued_song_download", null=True, on_delete=models.CASCADE
    )
    album = models.ForeignKey(
        Album, related_name="queued_album_download", null=True, on_delete=models.CASCADE
    )
    artist_profile = models.ForeignKey(
        Profile, related_name="queued_artist_tips", null=True, on_delete=models.CASCADE
    )

    def jsonify(self, request):
        if self.song:
            return self.song.jsonify(request)
        elif self.album:
            return self.album.jsonify(request)
        elif self.artist_profile:
            return self.artist_profile.jsonify(request)


class QueuedPlay(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    index = models.IntegerField(null=True)
    song = models.ForeignKey(
        Song, related_name="queued_plays", null=True, on_delete=models.CASCADE
    )
    radio = models.ForeignKey(
        Radio, related_name="queued_radio", null=True, on_delete=models.CASCADE
    )
    album = models.ForeignKey(
        Album, related_name="queued_album", null=True, on_delete=models.CASCADE
    )

    def jsonify(self, request):
        if self.song:
            return self.song.jsonify(request)
        if self.album:
            return self.album.jsonify(request)
        if self.radio:
            return self.radio.jsonify(request)

    # TODO: DEPRECATED
    def get_type(self):
        if self.song:
            return "song"
        elif self.radio:
            return "radio"
        else:
            return "album"

    class Meta:
        unique_together = (("profile", "song"),)


class Play(models.Model):
    # TODO: new records into this model aren't recorded anywhere at the moment
    # however, we do record 'listens' which is effective the same on a per second basis
    # which can be aggregate for the number of seconds listened to
    # However, since we have a post save signal for the Play model
    # we need to start using this or fix the Listens model to use the same
    # notifications
    timestamp = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(Profile, on_delete=models.CASCADE)
    played_song = models.ForeignKey(
        Song, related_name="plays", on_delete=models.CASCADE
    )
    radio = models.ForeignKey(
        Radio, related_name="plays", null=True, on_delete=models.CASCADE
    )
    album = models.ForeignKey(
        Album, related_name="plays", null=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return "player: %s, type: %s" % (self.player, self.get_play_type())

    def get_play_type(self):
        if self.radio:
            return "radio"
        elif self.album:
            return "album"
        else:
            return "song"


def create_feed_for_played_items(sender, **kwargs):
    if kwargs["created"]:
        play = kwargs["instance"]
        if play.radio:
            Feed.notify_played_radio(
                from_profile=play.player, to_profile=play.radio.profile, item=play
            )
        elif play.album:
            Feed.notify_played_album(
                from_profile=play.player, to_profile=play.album.profile, item=play
            )
        elif play.played_song:
            Feed.notify_played_song(
                from_profile=play.player, to_profile=play.played_song.profile, item=play
            )


post_save.connect(create_feed_for_played_items, Play)


class PlayerState(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    volume = models.IntegerField(null=True)

    # TODO: review, don't think this is used anywhere
    offset = models.IntegerField(null=True)
