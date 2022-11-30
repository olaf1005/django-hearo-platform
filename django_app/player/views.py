import logging
import json

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Profile
from media.models import Radio, Song, Album
from player.models import QueuedPlay, Play, PlayerState
from payment_processing.models import CreditCard

from utils import OrderedSet


logger = logging.getLogger(__name__)


def update_playlist_with_session(request):
    if not request.user.is_anonymous and "playlist" in request.session:
        playlist = request.session["playlist"]
        p = request.user.person.view
        for i, song_id in enumerate(playlist):
            s = Song.objects.get(id=song_id)
            if not QueuedPlay.objects.filter(profile=p, song=s).count():
                qp = QueuedPlay(profile=p, song=s, index=i)
                logger.info("song_play", {"song_title": s.title})
                qp.save()
        del request.session["playlist"]
        request.session.modified = True


def obj_info(request):
    if request.GET.get("id", False):
        id_ = request.GET["id"]
        if request.GET["type"] == "song":
            obj = Song.objects.get(id=id_)
        elif request.GET["type"] == "album":
            obj = Album.objects.get(id=id_)
        return HttpResponse(json.dumps(obj.jsonify(request)))
    else:
        return HttpResponse("Error: requires argument 'sid'")


@csrf_exempt
def load_cards(request):
    u = request.user
    if u.is_anonymous:
        return HttpResponse(json.dumps({"anon": True, "cards": []}))
    else:
        info = []
        cards = CreditCard.objects.filter(user=u)
        for c in cards:
            info.append(
                {
                    "stripe_id": c.stripe_id,
                    "card_type": c.cardType,
                    "last4": c.last4,
                    "id": c.pk,
                }
            )
    output = {"cards": info}
    return HttpResponse(json.dumps(output))


@csrf_exempt
def add_play(request):
    if request.method == "POST":
        id_ = request.POST["id"]
        i = request.POST["index"]
        update_playlist_with_session(request)
        if request.user.is_anonymous:
            if "playlist" not in request.session:
                playlist = OrderedSet()
            else:
                playlist = request.session["playlist"]
            if request.POST["type"] == "song":
                song = Song.objects.get(id=id_)
                playlist.add(song.id)
            else:
                album = Album.objects.get(id=id_)
                for song in album.get_online_songs():
                    playlist.add(song.id)
            request.session["playlist"] = OrderedSet(playlist)
            return HttpResponse()
        else:
            p = request.user.person.view
            if request.POST["type"] == "song":
                s = Song.objects.get(id=id_)
                if not QueuedPlay.objects.filter(profile=p, song=s).count():
                    qp = QueuedPlay(profile=p, song=s, index=i)
                    logger.info("song_play", {"song_title": s.title})
                    qp.save()
            else:
                album = Album.objects.get(id=id_)
                for song in album.get_online_songs():
                    if not QueuedPlay.objects.filter(profile=p, song=s).count():
                        qp = QueuedPlay(profile=p, song=song, index=i)
                        i += 1
                        qp.save()
                logger.info("album_play", {"album_title": album.title})
            return HttpResponse(status=200)
    else:
        return HttpResponse("requires POST request")


@csrf_exempt
def remove_play(request):
    if request.method == "POST":
        id_ = request.POST["id"]
        i = request.POST["index"]
        if request.user.is_anonymous:
            if "playlist" not in request.session:
                playlist = OrderedSet()
            else:
                playlist = request.session["playlist"]
            if request.POST["type"] == "song":
                s = Song.objects.get(id=id_)
                playlist.remove(s.id)
            return HttpResponse()
        else:
            p = request.user.person.view
            if request.POST["type"] == "song":
                s = Song.objects.get(id=id_)
                qp = QueuedPlay.objects.filter(profile=p, song=s, index=i)
            elif request.POST["type"] == "radio":
                r = Radio.objects.get(id=id_)
                qp = QueuedPlay.objects.filter(profile=p, radio=r, index=i)
            else:
                a = Album.objects.get(id=id_)
                qp = QueuedPlay.objects.filter(profile=p, album=a, index=i)
            qp.delete()
            return HttpResponse()
    else:
        return HttpResponse("requires POST request")


@csrf_exempt
def load_plays(request):
    if request.user.is_anonymous:
        output = {"anon": True, "volume": request.session.get("volume")}
    else:
        p = request.user.person.view
        qps = QueuedPlay.objects.filter(profile=p).order_by("index")
        output = {}
        output["media"] = []
        for qp in qps:
            if qp.get_type() == "song":
                output["media"].add(qp.song.jsonify(request))
            elif qp.get_type() == "radio":
                output["media"].add(qp.radio.jsonify(request))
            else:
                output["media"].add(qp.album.jsonify(request))
        try:
            ps = PlayerState.objects.get(profile=p)
            output["volume"] = ps.volume
        except PlayerState.DoesNotExist:
            pass
    return HttpResponse(json.dumps(output))


@csrf_exempt
@login_required
def history(request):
    if request.method == "POST":
        song_id = request.POST["id"]
        p = request.user.person.view
        s = Song.objects.get(id=song_id)
        play = Play(player=p, played_song=s)
        if request.POST.get("type", False) == "album":
            play.album = Album.objects.get(id=request.POST["collectionId"])
        elif request.POST.get("type", False) == "radio":
            play.radio = Radio.objects.get(id=request.POST["collectionId"])
        play.save()

        # Note: could update the song right now, but I don' think it's strictly
        # necessary
        # s.save(update=True)

        return HttpResponse()
    else:
        # Don't think GET is ever used but I could see where eventually we'd
        # use it for analytics?  Tentatively leaving it in
        p = request.user.person.view
        plays = Play.objects.filter(player=p)
        out = {}
        for play in plays:
            out[str(play.timestamp)] = play.played_song.title
        return HttpResponse(json.dumps(out))


@csrf_exempt
def update_playqueue_indices(request):
    if request.method == "POST":
        p = request.user.person.view
        if request.POST.get("indices", False):
            indices = json.loads(request.POST["indices"])
            qps = []

            for index in indices:
                try:
                    qps.add(QueuedPlay.objects.get(profile=p, index=index))
                except QueuedPlay.DoesNotExist as e:
                    logger.error(str(e), extra={"request": request})
                    return HttpResponse()
            for ind in range(len(indices)):
                qp = qps[ind]
                qp.index = ind
                qp.save()
        else:
            qps = QueuedPlay.objects.filter(profile=p).order_by("index")
            if qps.count() == 0:
                return HttpResponse()
            for i in range(qps.count()):
                qps[i].index = i
                qps[i].save
        return HttpResponse()


@login_required  # type: ignore
def radio_songs(request):
    "Returns a few songs to add to radio station every time it runs low."
    if request.method == "GET" and request.GET.get("id", False):
        _id = request.GET["id"]
        p = Radio.objects.get(id=_id).profile
        max_total = 6
        out = [song.jsonify(request) for song in p.get_radio_songs()[:max_total]]
        return HttpResponse(json.dumps(out))


def radio_available(prof_id):
    p = Profile.objects.get(id=prof_id)
    # parameters are semi arbitrary, trying to get a low depth but still high
    # chance that if there is something it will show up
    if len(p.get_radio_songs(2, 3, 2)):
        return True
    else:
        return False


def radio_info(request):
    if request.method == "GET" and "uid" in request.GET:
        radio = Radio.objects.get(profile__id=request.GET["uid"])
        return HttpResponse(json.dumps(radio.jsonify(request)))


@csrf_exempt
@login_required
def update_player_state(request):
    if request.method == "POST" and "volume" in request.POST:
        volume = request.POST["volume"]
        profile = request.user.person.view
        try:
            ps = PlayerState.objects.get(profile=profile)
            ps.volume = int(volume)
        except PlayerState.DoesNotExist:
            ps = PlayerState.objects.create(profile=profile, volume=volume)
        ps.save()
        return HttpResponse()


@login_required
def init_socket(request):
    if request.method == "GET":
        profile_id = request.user.person.view.id
        return HttpResponse(json.dumps({"room_name": "timesocket", "id": profile_id}))
