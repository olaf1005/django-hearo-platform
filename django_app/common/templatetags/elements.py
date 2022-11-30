"""
Inclusion tags for common elements used in most templates.
To use in a new template, prepend tag {% load elements %}
"""
import logging
import os
from operator import attrgetter
import json
import datetime
import uuid

from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template import Library
from django.conf import settings
import settings.utils as setting_utils
from accounts.models import Profile, SongFanEvent, AlbumFanEvent, Organization
from accounts.models import Review, Membership
from accounts import DEF_MUSICLISTING_IMG
from events.models import Event, FanEvent
from media.models import Song, Album, MusicUpload
from utils import parameterize, unparameterize
import exchange_utils


logger = logging.getLogger(__name__)

register = Library()


@register.inclusion_tag("common/repeater.html")
def exchange_token_dollar_value():
    try:
        avg_exchange_price = exchange_utils.exchange_token_dollar_value()
    except exchange_utils.DeterminingExchangeRateError:
        avg_exchange_price = "Unable to determine rate"
    return {"value": avg_exchange_price}


@register.inclusion_tag("common/repeater.html")
def jam_per_minute():
    try:
        value = round(exchange_utils.jam_per_minute(), 3)
    except Exception:
        value = "Temporarily unavailable"
    return {"value": value}


@register.filter
def token_jam_value_of_seconds(seconds) -> float:
    try:
        seconds = float(seconds)
        return round((float(seconds) / 60) * exchange_utils.jam_per_minute(), 8)
    except Exception:
        return 0


@register.filter
def token_jam_value(val) -> float:
    try:
        val = float(val)
        return val / settings.TOKEN_MULTIPLIER
    except Exception:
        return 0


@register.filter
def token_dollar_value(val) -> float:
    try:
        val = float(val)
        return round(
            token_jam_value(val) * exchange_utils.exchange_token_dollar_value(), 2
        )
    except Exception:
        return 0


@register.filter
def sub_space(val):
    return val.replace(" ", "")


@register.filter
def parameterize_val(val):
    return parameterize(val)


@register.filter
def unparameterize_val(val):
    return unparameterize(val)


@register.filter
def jsonify(obj):
    if isinstance(obj, QuerySet):
        return serialize("json", obj)
    return json.dumps(obj)


@register.inclusion_tag("common/fanbutton.html")
def fanbutton(element, objectid, viewer=None):
    """
    Standard-sized fan button. Flexible input:

    Parameters:
        object (Song, Album, or Profile): Parent object
        viewer (Profile): current logged-in viewer (fan button is relative to
        whether they have fanned this)

    OR

    Parameters:
        type (str): 'album', 'song', or 'profile'
        id (int): unique id for parent item
        viewer (Profile): current logged-in viewer (fan button is relative to
        whether they have fanned this)

    """

    logger.debug("element: %s, objectid: %s, viewer: %s", element, objectid, viewer)

    if isinstance(element, (Song, Album, Profile, Event)):
        viewer = objectid

        if isinstance(element, Song):
            typeof, fanned = (
                "song",
                SongFanEvent.objects.filter(faned_song=element, faner=viewer).exists()
                if viewer
                else False,
            )
        elif isinstance(element, Album):
            typeof, fanned = (
                "album",
                AlbumFanEvent.objects.filter(faned_album=element, faner=viewer).exists()
                if viewer
                else False,
            )
        elif isinstance(element, Profile):
            typeof, fanned = (
                "profile",
                element.fans.filter(pk=viewer.id).exists() if viewer else False,
            )
        elif isinstance(element, Event):
            typeof, fanned = (
                "event",
                FanEvent.objects.filter(fanner=viewer, fanned_event=element)
                if viewer
                else False,
            )
            logger.debug(fanned)
        else:
            return False
    else:
        if element == "song":
            element, typeof = Song.objects.get(id=objectid), "song"
            fanned = (
                SongFanEvent.objects.filter(faned_song=element, faner=viewer).exists()
                if viewer
                else False
            )

        elif element == "album":
            element, typeof = Album.objects.get(id=objectid), "album"
            fanned = (
                AlbumFanEvent.objects.filter(faned_album=element, faner=viewer).exists()
                if viewer
                else False
            )

        elif element == "profile":
            element, typeof = Profile.objects.get(id=objectid), "profile"
            fanned = element.fans.filter(pk=viewer.id).exists() if viewer else False
        else:
            return False

    values = {
        "type": typeof,
        "fanned": fanned,
        "id": element.id,
    }
    return values


@register.inclusion_tag("common/percentage_membership_split.html")
def percentage_membership_split(profile, group_id):
    person_id = profile.person.id
    try:
        split = Membership.objects.filter(group_id=group_id, person_id=person_id)[
            0
        ].revenue_split
    except Exception:
        split = 0.0
    return {"person_id": person_id, "group_id": group_id, "split": split}


@register.inclusion_tag("common/sharebutton.html")
def sharebutton(song):
    """
    Share a song

    Requires a unique id to split songs displayed multiple times on the
    display.
    """
    values = {
        "profile": song.profile,
        "song": song,
        "id": str(uuid.uuid1()).split("-")[0],
        "BASE_URL": settings.BASE_URL,
    }
    return values


@register.inclusion_tag("common/feed-post.html")
def feedpost(feed, view):
    disallow_feed_types = ["weekly_digest", "monthly_digest", "yearly_digest"]
    return {"feed": feed, "view": view, "disallow_feed_types": disallow_feed_types}


@register.inclusion_tag("common/profilereview.html")
def profilereview(review):
    return {
        "review": review,
    }


@register.inclusion_tag("common/event.html")
def event(event):
    return {
        "event": event,
    }


@register.inclusion_tag("common/album_admin_view.html")
def album_admin_view(album):
    return {
        "album": album,
    }


@register.inclusion_tag("common/reviewbutton.html")
def reviewbutton(element, view=None):
    """
    Review button for songs and albums

    Parameters:
        element (Song or Album): The review button is for this media object
    """

    typeof = {Song: "song", Album: "album", Profile: "profile"}[type(element)]

    count = 0
    profile = None

    if typeof == "song":
        count = Review.objects.filter(song=element).count()
        profile = element.profile.keyword
    elif typeof == "album":
        count = Review.objects.filter(album=element).count()
        profile = element.profile.keyword
    elif typeof == "profile":
        count = Review.objects.filter(profile=element).count()
        profile = element.keyword

    data = {
        "element": element,
        "type": typeof,
        "id": element.id,
        "count": count,
        "view": view,
        "profile": profile,
    }

    if isinstance(element, Profile):
        data["title"] = element.name
    else:
        data["title"] = element.title

    return data


@register.inclusion_tag("common/tipbutton.html")
def tipbutton(profile):
    """
    Tip button for profiles

    Parameters:
        profile (Profile) tip button for this profile
    """

    return {"id": profile.id}


@register.inclusion_tag("common/mail.html")
def mail(profile, right="20px", top="12px"):
    return {"profile": profile, "right": right, "top": top}


@register.inclusion_tag("common/fanmail-button.html")
def fanmailbutton(profile):
    """
    Fanmail a profile

    Parameters:
        profile: Profile
    """
    return {"profile": profile}


@register.inclusion_tag("common/downloadbutton.html")
def downloadbutton(element):
    """
    Download button for songs and albums

    Parameters:
        element (Song or Album): The download button is for this media object
    """
    return {"type": {Song: "song", Album: "album"}[type(element)], "element": element}


@register.inclusion_tag("common/tixbutton.html")
def tixbutton(event):
    return {"event": event}


@register.inclusion_tag("common/usertab.html")
def usertab(profile):
    """
    Usertab element

    Parameters:
    profile (Profile): The download button is for this media object
    """
    return {"profile": profile}


@register.inclusion_tag("common/userlisting-short.html")
def userlistingShort(profile):
    """
    Usertab element

    Parameters:
        profile (Profile): The download button is for this media object
    """
    return {"profile": profile}


@register.inclusion_tag("common/music.listing.html")
def musiclisting(entity, view):
    """
    Music listing element, which can represent any musical entity (or a fan even)

    Parameters:
        entity: a MusicUpload or Profile
        view: a Profile or None for anon user
    """

    if isinstance(entity, MusicUpload):
        entity_type = "song" if isinstance(entity, Song) else "album"
        image = str(entity.get_artwork()).lstrip("/")
        title = entity.title
        subtitle = "by %s" % entity.profile.name
        profileurl = "/profile/%s" % entity.profile.get_absolute_url()
        play_button_type = entity_type
        play_button_id = entity.id

    elif isinstance(entity, (Profile, Organization)):
        entity_type = "artist"
        title = entity.name
        subtitle = entity.location or ""
        image = entity.get_music_listing_img() or DEF_MUSICLISTING_IMG
        image = str(image).lstrip("/")
        profileurl = entity.get_absolute_url()
        # if entity.person.is_musician:
        if Song.objects.filter(profile=entity).count() > 0:
            play_button_id = entity.get_music_listing_songid()
            play_button_type = "song"
        else:
            play_button_id = None
            play_button_type = None
    else:
        # Fix for https://app.getsentry.com/hearo-team/hearo/issues/104888408/
        # If entity type is not recognized, we shouldn't display it
        # (The underlying issue that causes a empty entity to pass has not been
        # fixed)
        return {}

    return {
        "title": title,
        "subtitle": subtitle,
        "image": image,
        "profileurl": profileurl,
        "entity_type": entity_type,
        "play_button_type": play_button_type,
        "play_button_id": play_button_id,
        "entity": entity,
        "view": view,
    }


@register.inclusion_tag("common/show.listing.html")
def showlisting(event, view):
    """Show listing element, which can represent any musical entity (or a fan
    even)
    """

    featured_prof = sorted(
        event.artists.all(), key=attrgetter("rank_all"), reverse=True
    )[0]

    return {
        "event": event,
        "featured": featured_prof,
        "month": event.starts.strftime("%b"),
        "day": event.starts.strftime("%d"),
        "time": event.starts.strftime("%I:%M"),
        "artists": event.artists.all(),
        "venuelink": "/profile/%s" % event.venue.getProfile().keyword,
        "artists_no_space": [a.name.replace(" ", "") for a in event.artists.all()],
        "view": view,
    }


@register.inclusion_tag("common/show.listing.big.html")
def showlistingbig(event, view):
    """Show listing element, which can represent any musical entity (or a fan
    even)

    """

    featured_prof = sorted(
        event.artists.all(), key=attrgetter("rank_all"), reverse=True
    )[0]

    return {
        "event": event,
        "featured": featured_prof,
        "month": event.starts.strftime("%b"),
        "day": event.starts.strftime("%d"),
        "time": event.starts.strftime("%I:%M"),
        "artists": event.artists.all(),
        "view": view,
    }


@register.inclusion_tag("common/calendar.page.html")
def calendar_page(mo, day):
    return {"mo": mo, "day": day}


@register.inclusion_tag("common/time.display.html")
def time_display(time):
    return {
        "time": time,
    }


@register.inclusion_tag("common/album.listing.html")
def albumlisting(album, view, expanded=False):
    default_img = "public/images/defaults/album.png"
    track_count = album.get_online_songs().count()
    track_count = "%s track%s" % (track_count, "" if track_count == 1 else "s")

    return {
        "album": album,
        "title": album.title,
        "release_year": album.year_released,
        "track_count": track_count,
        "byline": "by %s" % album.profile.name,
        "profileurl": album.profile.get_absolute_url(),
        "cover": album.medium_cover or default_img,
        "play_button_id": album.id,
        "expanded": expanded,
        "songs": album.get_online_songs,
        "view": view,
    }


@register.inclusion_tag("common/badge.html")
def badge(badgeClass, badgeText):
    return {"badgeClass": badgeClass, "badgeText": badgeText}


@register.inclusion_tag("common/dir_usertab.html")
def dir_usertab(profile):
    """
    Usertab element

    Parameters:
        profile (Profile): The download button is for this media object
    """

    return {"profile": profile}


@register.inclusion_tag("common/empty.html")
def empty_message(
    profile, viewer, topic, actionlink="/my-account/", actionverb="Create"
):
    """
    Empty message for media box

    Parameters:
        person (Profile): profile being viewed
        viewer (Profile): logged in user
    """
    an = topic[0].lower() in list("aeiou")
    return {
        "profile": profile,
        "viewer": viewer,
        "topic": topic,
        "actionlink": actionlink,
        "actionverb": actionverb,
        "an": an,
    }


@register.inclusion_tag("common/fandlib_empty.html")
def empty_fandlib_message(
    profile, viewer, topic, conditional=False, actionlink="/music"
):
    """
    Empty message for fandlib box

    Parameters:
        person (Profile): profile being viewed
        viewer (Profile): logged in user
    """
    logger.debug("conditional %s, topic %s", conditional, topic)
    an = topic[0].lower() in list("aeiou")
    return {
        "profile": profile,
        "viewer": viewer,
        "topic": topic,
        "actionlink": actionlink,
        "none_conditional": bool(conditional),
        "an": an,
    }


@register.inclusion_tag("common/videolisting.html")
def videolisting(video):
    """
    video listing for dashboard video tab.

    Parameters:
        video (Video object)
    """
    return {"video": video}


@register.inclusion_tag("common/songlisting_div.html")
def songlisting(song, viewer, admin=False):
    """
    Song listing for media/fandlib boxes. Also in use in the albumtracks tag

    Parameters:
        song (Song)
        viewer (Profile): logged in user
        [profile] (Profile): artist, if you want a usertab in it
        (omit when it's the logged-in user's stuff)
    """
    # fanned = (viewer and SongFanEvent.objects.filter(faned_song=song, faner=viewer))
    values = {
        "song": song,
        "view": viewer,
        "admin": admin,
    }
    logger.debug(values)
    return values


@register.inclusion_tag("common/songlisting.pending.html")
def songlisting_pending():
    """
    Pending song listing for songs being uploaded.

    No parameters. This template is just static HTML that gets modified by
    JavaScript on upload.
    """
    return {}


@register.filter
def format_seconds_to_mmss(seconds):
    try:
        minutes = seconds // 60
        seconds %= 60
        return "%2i:%02i" % (minutes, seconds)
    except Exception:
        return ""


@register.inclusion_tag("common/songlisting_div.html")
def songlisting_admin(song):
    return songlisting(song, song.profile, admin=True)


@register.inclusion_tag("common/userlisting.html")
def userlisting(profile, viewer):
    """
    User listing for directory/search/fandlib

    Parameters:
        profile (Profile)
        viewer (Profile): logged in user
    """
    values = {"profile": profile, "view": viewer}
    return values


@register.inclusion_tag("common/downloadlisting.html")
def downloadlisting(media, viewer):
    """
    Download listing for in the download tab

    Parameters:
        media (Song)
        viewer (Profile): logged in user
    """

    fanned = False
    if Song.objects.filter(musicupload_ptr=media).exists():
        if viewer and SongFanEvent.objects.filter(
            faned_song=media.media_song, faner=viewer
        ):
            fanned = True
        _type = "song"
        media = media.media_song

    else:
        if viewer and AlbumFanEvent.objects.filter(
            faned_album=media.media_album, faner=viewer
        ):
            fanned = True
        media = media.media_album
        _type = "album"
    values = {"media": media, "view": viewer, "type": _type, "fanned": fanned}
    logger.debug(values)
    return values


@register.inclusion_tag("common/albumtracks.html")
def albumbrowser(album, viewer, profile=None):
    """
    Album view with cover/title and traffic light buttons on top.

    Parameters:
        album (Album)
        viewer (Profile): logged in user
        [profile] (Profile): artist, if you want usertabs in the song listings
        (omit when it's the logged-in user's stuff)
    """

    fanned = bool(
        viewer and AlbumFanEvent.objects.filter(faned_album=album, faner=viewer)
    )
    values = {
        "album": album,
        "view": viewer,
        "fanned": fanned,
        "songs": album.songs.all().order_by("track_num"),
        "cover": album.medium(),
    }
    if profile:
        values["profile"] = profile
    return values


@register.inclusion_tag("common/albumtile.html")
def albumtile(album, viewer):
    """
    Album cover tile, which when clicked opens the albumbrowser for that album

    Parameters:
        album (Album)
        viewer (Profile): logged in user
        title: album title
    """

    values = {
        "album": album,
        "cover": album.medium(),
        "title": album.title,
        "view": viewer,
    }
    return values


@register.inclusion_tag("common/fanmail_message.html")
def fanmail_message(message):
    """
    Fanmail message listing, in the inbox

    Parameters:
        sender (Profile): who sent the message
        subject (str)
        message (str)
        to (Profile)
        timestamp (datetime)
        read (bool)
    """
    now = datetime.datetime.now()

    # Convert the datetime to a semantic string.
    # %s conditional is here to include year only if it's not the current year
    if message.timestamp.year != now.year:
        timestamp_string = message.timestamp.strftime("%B %d %Y at %I:%M %p")
    else:
        timestamp_string = message.timestamp.strftime("%B %d at %I:%M %p")

    html = message.from_profile.id == settings.HEARO_TEAM_PROFILE_ID

    values = {"timestamp": timestamp_string, "message": message, "html": html}

    return values


@register.inclusion_tag("common/to_fanmail_message.html")
def to_fanmail_message(message):
    """
    Fanmail message listing, in the inbox

    Parameters:
        sender (Profile): who sent the message
        subject (str)
        message (str)
        timestamp (datetime)
        read (bool)
    """
    now = datetime.datetime.now()
    # Convert the datetime to a semantic string.
    # %s conditional is here to include year only if it's not the current year
    if message.timestamp.year != now.year:
        timestamp_string = message.timestamp.strftime("%B %d %Y at %I:%M %p")
    else:
        timestamp_string = message.timestamp.strftime("%B %d at %I:%M %p")

    values = {"timestamp": timestamp_string, "message": message}

    return values


@register.inclusion_tag("common/empty.media.message.html")
def empty_media_message(thing, name, own):
    return {"thing": thing, "name": name, "own": own}


@register.inclusion_tag("common/mustache_partials.html")
def mustache_partials():
    partials_dir = setting_utils.project_path("templates/partials")
    partials_export = []

    for root, dirs, partials in os.walk(partials_dir):
        for partial in partials:
            source = open("%s/%s" % (partials_dir, partial), "r")
            partials_export.append((partial.replace(".mustache", ""), source.read()))
            source.close()
    return {"partials": partials_export}
