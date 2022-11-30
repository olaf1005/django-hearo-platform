from django.template import loader

from media.models import Song
from player.models import Play
from accounts.models import Profile

from utils import render_appropriately


def songs(request):
    all_songs = Song.objects.filter(processing=False, deleted=False)
    trios = [(s.title, s.profile.keyword, s.plays.count()) for s in all_songs]
    trios = sorted(trios, key=lambda p: p[2] * -1)
    t = loader.get_template("dash/songs.html")
    return render_appropriately(request, t, {"trios": trios})


def players(request):
    all_plays = Play.objects.all()
    all_players = {}
    for play in all_plays:
        keyword = play.player.keyword
        if keyword not in all_players:
            all_players[keyword] = 1
        else:
            all_players[keyword] += 1
    pairs = sorted(list(all_players.items()), key=lambda p: p[1] * -1)

    t = loader.get_template("dash/players.html")
    return render_appropriately(request, t, {"pairs": pairs})


def newest_songs(request):
    songs = Song.objects.all().order_by("-id")[:50]
    t = loader.get_template("dash/newest_songs.html")
    return render_appropriately(request, t, {"songs": songs})


def newest_profiles(request):
    profiles = Profile.objects.all().order_by("-id")[:50]
    t = loader.get_template("dash/newest_profiles.html")
    return render_appropriately(request, t, {"profiles": profiles})
