from django.http import HttpResponse

from utils import JSON, ajax_login_required, OrderedSet, ajax_login_required_no_error
from media.models import Song, Album
from player.models import QueuedDownload, QueuedPlay
from player.views import update_playlist_with_session
from apiv0.decorator import api_v0
from accounts.models import Profile


@ajax_login_required_no_error
@api_v0
def downloads(request, profile):
    if request.method == "GET":
        return downloads_GET(request, profile)
    elif request.method == "POST":
        return downloads_POST(request, profile)
    elif request.method == "DELETE":
        return downloads_DELETE(request, profile)


def downloads_GET(request, profile):
    # Get all items
    queued = QueuedDownload.objects.filter(profile=profile).order_by("timestamp")
    return JSON([qd.jsonify(request) for qd in queued])


def downloads_POST(request, profile):
    # Add new item
    if request.POST["type"] == "song":
        song = Song.objects.get(id=request.POST["id"])
        existing, created = QueuedDownload.objects.get_or_create(
            profile=profile, song=song
        )
    elif request.POST["type"] == "album":
        album = Album.objects.get(id=request.POST["id"])
        existing, created = QueuedDownload.objects.get_or_create(
            profile=profile, album=album
        )
    elif request.POST["type"] == "profile":
        artist_profile = Profile.objects.get(id=request.POST["id"])
        existing, created = QueuedDownload.objects.get_or_create(
            profile=profile, artist_profile=artist_profile
        )
    return HttpResponse(status=201)


@ajax_login_required
@api_v0
def downloads_DELETE(request, profile, item_id, item_type):
    # Delete item
    existing = None
    if item_type == "song":
        song = Song.objects.get(id=item_id)
        existing = QueuedDownload.objects.filter(profile=profile, song=song)
    elif item_type == "album":
        album = Album.objects.get(id=item_id)
        existing = QueuedDownload.objects.filter(profile=profile, album=album)
    elif item_type == "profile":
        artist_profile = Profile.objects.get(id=item_id)
        existing = QueuedDownload.objects.filter(
            profile=profile, artist_profile=artist_profile
        )

    if existing:
        existing.delete()
    return HttpResponse(status=204)


@api_v0
def playlist(request, profile):
    if request.method == "GET":
        return playlist_GET(request, profile)
    elif request.method == "POST":
        if "song_id" in request.POST:
            return playlist_POST_song(request, profile)
        elif "album_id" in request.POST:
            return playlist_POST_album(request, profile)
        elif "artist_profile_id" in request.POST:
            return playlist_POST_artist_profile(request, profile)


def playlist_GET(request, profile):
    update_playlist_with_session(request)
    if request.user.is_anonymous:
        if "playlist" not in request.session:
            playlist = OrderedSet()
        else:
            playlist = request.session["playlist"]
        queuedplay = []
        for song_id in playlist:
            try:
                song = Song.objects.get(pk=song_id)
            except Song.DoesNotExist:
                pass
            else:
                queuedplay.append(song.jsonify(request))
        queuedplay.reverse()
        request.session["playlist"] = playlist
    else:
        playlist = QueuedPlay.objects.filter(profile=profile).order_by("timestamp")
        queuedplay = [qp.jsonify(request) for qp in playlist]
    return JSON(queuedplay)


def playlist_POST_song(request, profile):
    song = Song.objects.get(id=request.POST["song_id"])
    if request.user.is_anonymous:
        if "playlist" not in request.session:
            playlist = OrderedSet()
        else:
            playlist = request.session["playlist"]
        playlist.add(song.id)
        request.session["playlist"] = playlist
    else:
        existing, created = QueuedPlay.objects.get_or_create(profile=profile, song=song)
    return HttpResponse(status=201)


def playlist_POST_album(request, profile):
    album = Album.objects.get(id=request.POST["album_id"])
    if request.user.is_anonymous:
        if "playlist" not in request.session:
            playlist = OrderedSet()
        else:
            playlist = request.session["playlist"]
        for song in album.songs.all():
            playlist.add(song.id)
        request.session["playlist"] = playlist
    else:
        for song in album.songs.all():
            existing, created = QueuedPlay.objects.get_or_create(
                profile=profile, song=song
            )
    return HttpResponse(status=201)


def playlist_POST_artist_profile(request, profile):
    artist_profile = Profile.objects.get(id=request.POST["artist_profile_id"])
    existing, created = QueuedPlay.objects.get_or_create(
        profile=profile, artist_profile=artist_profile
    )
    return HttpResponse(status=201)


@api_v0
def playlist_DELETE(request, profile, song_id):
    song = Song.objects.get(id=song_id)
    if request.user.is_anonymous:
        if "playlist" not in request.session:
            playlist = OrderedSet()
        else:
            playlist = request.session["playlist"]
        playlist.remove(song.id)
        request.session["playlist"] = playlist
    else:
        existing = QueuedPlay.objects.filter(profile=profile, song=song)
        existing.delete()
    return HttpResponse(status=204)
