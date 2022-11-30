Prerequisites
=============

The **activity** application uses the [http://code.playfire.com/django-email-from-template](django-email-from-template) library to organize notification email templates.

Add two new entries in your **settings.py**:

    INSTALLED_APPS = (
        ...
        'activity',
        'email_from_template',
    )

DeliverNotifications
====================

This job will fetch all Feed entries that have not been delivered. To do that,
it queries the database for rows where **delivered_at** is **NULL**.

Then it will send out the notification email and mark the feed as delivered.

Feeds
=====

Feeds is a library that allows any existing system action to create a new
activity feed entry.

Activity feeds are mainly used for sending notification emails, but it can be
easily reused for an activity feed by affected user or by target item.

Each activity feed entry has the following fields:

* __feed_type__ - the type of the activity (see below)
* __from_profile__ - the originator of the feed (user who initiated the activity)
* __to_profile__ - the user affected by the activity of the feed
* __item__ - the item that was created as a result of this activity
* __delivered_at__ - controls whether or not this activity email was sent (null if not yet sent)

So we can have an example feed, where __User1__ played the song __Angel__ by
__User2__.

So that can be represented by:

    Feed.create(feed_type='played_song', from_profile=user1, to_profile=user2, item=Play(played_song=...))

The offline scheduled process can then kick in and collect all entries where
__delivered_at__ is NULL and start processing them one by one.

In our exemple, that would trigger a new email to user represented by
__to_profile__, using the __played_song__ template. This template could
indicate the name of the song (from __item.played_song.title__, for instance)
and have a link to the song (from __item.played_song.id__).

    Hello User1,

    Your song <a href="http://hearo.fm/songs/194">Angel</a> was just played by <a href="http://hearo.fm/profile/2">User2</a>.

    Hearo.fm

Some emails will only be delivered if a configurable number of events of the
same type are pending. The **fan_user** email is an example of email that will
follow this pattern.

# Types of feeds

## __FAN_MAIL__ - When you get a fan mail

	from accounts.models import Profile

	import mail.models
	import feed.models

	# retrieves current user
	profile = Profile.objects.get(...)
	message = Message.objects.create(...)

	Feed.notify_fan_mail(from_profile=profile, to_profile=message.to_profile, item=message)

## __REVIEW__ - When you get a review

	import accounts.models

	# retrieves current user
	profile = Profile.objects.get(...)
	review  = Review.object.get(...)

	Feed.notify_review(from_profile=profile, to_profile=null, item=review)

__Question:__ What about song and album reviews?

## __TIP__ - When someone tips you

	# retrieves current user
	profile = Profile.objects.get(...)
	tip     = Tip.objects.create(...) # (?)

	Feed.notify_tip(from_profile=profile, to_profile=tip.profile, item=tip)

## When people fan a user/song/album

### __FAN_USER__ - When fans a user

	# faner => person who fanned someone (is fan of fanee)
	# fanee => person who is being fanned by someone (is the fanee of a fan)

	# retrieves the current user
	profile = Profile.objects.get(...)
	fan     = Fan.objects.create(fanee=profile, faner=...)

	Feed.notify_fan_user(from_profile=profile, to_profile=fan.fanee, item=fan)

### __FAN_SONG__ - When fans a song

	# retrieves the current user
	profile = Profile.objects.get(...)
	fan     = SongFanEvent.objects.create(...)

	Feed.notify_fan_song(from_profile=profile, to_profile=fan.faned_song.profile, item=fan)

### __FAN_ALBUM__ - When fans an album

    # retrieves the current user
    profile = Profile.objects.get(...)
    fan     = AlbunFanEvent.objects.create(...)

    Feed.notify_fan_album(from_profile=profile, to_profile=fan.faned_album.profile, item=fan)

### __FAN_EVENT__ - When fans an event

__Question:__ should we support this as well?

## When songs/albums/radio played

### __PLAYED_SONG__ - When a song is played

    # retrieves the current user
    profile = Profile.objects.get(...)
    play    = Play.objects.create(..., played_song=...)

    Feed.notify_played_song(from_profile=profile, to_profile=play.player, item=play) # we'll consider play.played_song in this case

### __PLAYED_ALBUM__ - When an album is played

    # retrieves the current user
    profile = Profile.objects.get(...)
    play    = Play.objects.create(..., album=...)

    Feed.notify_played_album(from_profile=profile, to_profile=play.player, item=play) # we'll consider play.album in this case

### __PLAYED_RADIO__ - When a radio is played

    # retrieves the current user
    profile = Profile.objects.get(...)
    play    = Play.objects.create(..., radio=...)

    Feed.notify_played_radio(from_profile=profile, to_profile=play.player, item=play) # we'll consider play.radio in this case

## __NEW_EVENT__ - When Artists you're a fan of post new shows (events) in your area

    # retrieves the current user
    profile = Profile.objects.get(...)
    event   = Event.objects.create(...)

    for artist in event.artists:
      for fan in artist.get_fans():
        # TODO: Confirm if this is enough or if we still want to narrow
        #       it also by geolocation, on top of being a fan
        Feed.notify_new_event(from_profile=profile, to_profile=play.player, item=play)
