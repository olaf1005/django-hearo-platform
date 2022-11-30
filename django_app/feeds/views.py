import logging
from datetime import timedelta, datetime
import multiprocessing

from django.http import HttpResponse
from django.db.models import Count
from django.template import loader

from accounts.models import Profile, Review
from media.models import Album, Song
from events.models import Event

import update_ranking
from utils import (
    JSON,
    get_objects_near,
    scrape_list,
    render_appropriately,
    ajax_login_required,
)


logger = logging.getLogger(__name__)

DEF_RANK = "-rank_week"


def init_values():
    """generates the default values for feeds"""
    # make sure anyone who wants to be private is private
    songs = Song.objects.filter(deleted=False, online=True)
    albums = Album.objects.filter(deleted=False)
    albums = albums.annotate(song_count=Count("songs")).filter(song_count__gte=1)

    artists = Profile.objects.all()
    # filter so only music profiles show up
    artists = artists.annotate(music_count=Count("music")).filter(music_count__gte=1)
    return (artists, albums, songs)


class FauxCache(object):
    def __init__(self, n=100, update_freq=5400):
        # 60*60*1.5 = 5400
        self.n = n
        # days,seconds, microseconds
        self.update_freq = timedelta(0, update_freq, 0)
        self.reset_cache()
        self.last_ranked = datetime.today()

    def reset_cache(self):
        n = self.n
        self.profiles, self.albums, self.songs = init_values()
        self.profiles = self.profiles.order_by(DEF_RANK)[:n]
        self.songs = self.songs.order_by(DEF_RANK)[:n]
        self.albums = self.albums.order_by(DEF_RANK)[:n]

    def get(self, start, stop):
        """uses cached results if possible, hits db if not enough"""
        # check to see if we need to reupdate
        if (datetime.today() - self.last_ranked - self.update_freq).days >= 0:
            self.update()

        if stop >= self.n:
            p, a, s = init_values()
            p = p.order_by(DEF_RANK)
            a = a.order_by(DEF_RANK)
            s = s.order_by(DEF_RANK)

            return p[start:stop], a[start:stop], s[start:stop]
        else:
            logging.debug("using cached data")
            return (
                self.profiles[start:stop],
                self.albums[start:stop],
                self.songs[start:stop],
            )

    def update(self):
        logging.debug("updating from feeds...")

        self.last_ranked = datetime.today()

        # reset our profiles (they will be one behind)
        self.reset_cache()
        multiprocessing.Process(target=update_ranking.update_all).start()


# singleton to store default querysets in memory
cache = FauxCache()


# @login_required (for anonymous user)
def index(request):
    t = loader.get_template("feeds/index.html")
    return render_appropriately(request, t, {"contentclass": "music"})


# DON'T FIND OBJECTS BY THEIR KEYWORD. AND DON'T USE OBJECTS.FILTER() WHEN YOU
# ARE LOOKING FOR ONE RESULT.
# I have no idea why the keyword even exists. Use their IDs - thats what
# they're meant for.
# <3 Artur


@ajax_login_required
def fan_ajax(request):
    "New fan and unfan functions"
    profile = request.user.person.view
    post = request.POST
    # Song? Artist? What are we fanning
    target = post["target"]

    model = {"song": Song, "album": Album, "profile": Profile, "event": Event}[target]
    event = fan(model, request, profile, post)

    # Log it
    data = {}
    fanned_object = model.objects.get(id=post["id"])

    if target in ["song", "album", "event"]:
        data["object"] = '%s\n"%s"\nby %s' % (
            target,
            fanned_object.title,
            fanned_object.profile.keyword,
        )
    else:
        data["object"] = "profile\n%s" % fanned_object.keyword
    logger.debug("unfanned" if post["unfan"] == "t" else "fanned", data)
    return event


def fan(Model, request, user, post):
    model = Model.objects.get(id=post["id"])
    if post["unfan"] == "t":
        model.remove_fan(user)
        model.save()
    else:
        model.add_fan(user)
        model.save()
    return HttpResponse(202)


@ajax_login_required
def review_ajax(request):
    profile = request.user.person.view
    if request.POST.get("review"):
        write_up = request.POST["review"]
        key = request.POST["keyword"]
        art = Profile.objects.filter(keyword=key).all()
        song = Song.objects.filter(keyword=key).all()
        alb = Album.objects.filter(keyword=key).all()
        if art:
            r = Review(review=write_up, reviewer=profile, profile=art[0])
        elif song:
            r = Review(review=write_up, reviewer=profile, song=song[0])
        elif alb:
            r = Review(review=write_up, reviewer=profile, album=alb[0])
        r.save()
        return HttpResponse("-")


def update_ajax(request):
    rg = request.GET

    start = int(rg["start"]) if "start" in rg else 0
    stop = int(rg["stop"]) if "stop" in rg else 20

    time = rg["time"]
    price = rg["price"]
    location = rg["location"]
    genre = rg["genre"]
    ranking = rg["ranking"]

    # cache default values
    if (
        ranking == "Hottest"
        and time == "Week"
        and price == "All Prices"
        and (not location)
        and (not genre)
    ):
        p, a, s = cache.get(start, stop)
        return jsonify_feeds(request, p, a, s)

    artists, albums, songs = init_values()
    # filter by price
    price_to_download_type = {
        "Free": "free",
        "NYP": "name_price",
        "Paid": "normal",
        "No Download": "none",
    }
    if price and price in price_to_download_type:
        songs = songs.filter(download_type=price_to_download_type[price])
        albums = albums.filter(download_type=price_to_download_type[price])

    # filter by location of artist!
    # NOTE: needs address in your location
    if location:
        artists = get_objects_near(Profile, artists, location.replace("Venue: ", ""))
    # filter by genre
    for g in scrape_list(genre):
        if g != "":
            artists = artists.filter(genres__name=g)

    # sort songs/albums by location/genres too!
    songs = songs.filter(profile__in=artists)
    albums = albums.filter(profile__in=artists)

    if ranking == "Hottest":
        r = {
            "Today": "-rank_today",
            "Week": "-rank_week",
            "Month": "-rank_month",
            "Year": "-rank_year",
            "All Time": "-rank_all",
        }[time]
    else:
        r = "-pk"

    artists = artists.order_by(r)
    artists = artists[start:stop]

    albums = albums.order_by(r)
    albums = albums[start:stop]

    songs = songs.order_by(r)
    songs = songs[start:stop]

    return jsonify_feeds(request, artists, albums, songs)


def jsonify_feeds(request, artists, albums, songs):
    return JSON(
        [
            request.user.is_authenticated,
            [artist.as_music_listing(request) for artist in artists],
            [album.as_music_listing(request) for album in albums],
            [song.as_music_listing(request) for song in songs],
        ]
    )
