from utils import JSON
from media.models import Song, Album
from accounts.models import Profile


def song(request, songid):
    sng = Song.objects.get(id=songid)
    return JSON(sng.jsonify(request))


def album(request, albumid):
    alb = Album.objects.get(id=albumid)
    return JSON(alb.jsonify(request))


def profile(request, profileid):
    prof = Profile.objects.get(id=profileid)
    return JSON(prof.jsonify(request))
