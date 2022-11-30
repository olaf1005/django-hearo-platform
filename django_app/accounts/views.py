import itertools
import datetime
import csv
import json
import logging
import re
import requests
import pgpy
import threading

from geopy import geocoders
from geopy.exc import GeocoderTimedOut, GeocoderQuotaExceeded, GeocoderServiceError

from django.http import (
    JsonResponse,
    StreamingHttpResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    Http404,
)
from django.urls import reverse, resolve
from django.utils import timezone
from django.core.mail import mail_admins
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.template import loader
from django.contrib.auth.models import UserManager
from django.contrib.auth import authenticate, login, logout
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, Sum
from django.core.files.images import ImageFile
from django.conf import settings
from django.contrib.auth.models import User
from accounts.forms import SendReceiveForm

from accounts.models import (
    HTSTokenTransfer,
    Membership,
    Profile,
    Person,
    Musician,
    StatusUpdate,
    Location,
    Review,
    Genre,
    Instrument,
    DownloadCharge,
    SongFanEvent,
    AlbumFanEvent,
    Band,
    Venue,
    Label,
    Organization,
    DEF_MUSICLISTING_IMG,
)
from payment_processing.models import Receipt, BankInfo
from mail.models import Message
from media.models import Photo, Song, Album, Video, Banner, Radio, Listen
from media import DownloadFormat
from activity.models import Feed
from events.models import Event, FanEvent
from player.views import radio_available, update_playlist_with_session
from worldmap.geography import COUNTRIES
from worldmap.views import get_secondary, get_country

import the_hearo_team

import utils
import hedera_utils
import openpgp_utils

from django.core.exceptions import ValidationError
from disposable_email_checker.validators import validate_disposable_email

import quickemailverification


logger = logging.getLogger(__name__)


def refresh_header(request):
    t = loader.get_template("header.html")
    return utils.render_appropriately(request, t, {})


def ping(request):
    rg = request.GET
    urls = json.loads(rg["urls"])
    ret = {}
    for url in urls:
        logger.info("pinging %s", url)
        r = resolve(url)
        logger.info(r)
        logger.info(r.func(request))
        # all functions called here return strict JSON
        try:
            data = r.func(request)
            ret.update(data)
        except Exception as e:
            logger.error("An error occurred in ping: %s", e)
            raise e
    return JsonResponse(ret)


def password_recovery(request):
    email = request.GET.get("email")
    t = loader.get_template("accounts/password-recovery.html")
    return utils.render_appropriately(request, t, {"email": email})


def send_recovery(request):
    if request.method == "POST":
        email = request.POST["email"]
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            new_password = UserManager().make_random_password()
            utils.sendemail_template(
                [email],
                "email_notifications/send_recovery.html",
                {"user": request.user, "new_password": new_password},
            )
            user.set_password(new_password)
            user.person.should_change_pass = True

            user.person.save()
            user.save()

            return HttpResponse("t")
    return HttpResponse("f")


def check_register_email(request):
    """
    input - email string in response
    output - HttpResponse boolean whether or not email is valid (django re)
    callers - registration on  hage javascript
    """
    email = request.GET["email"]
    if not utils.email_re.match(email):
        return HttpResponse("Invalid email!")
    if Profile.objects.filter(email_normalized=utils.normalize_email(email)).exists():
        # email exists
        return HttpResponse(
            "Email already registered, if its a gmail address make sure you haven't previously registered with a period or +"
        )
    if User.objects.filter(email=email).exists():
        return HttpResponse("Email in use already!")
    return HttpResponse("")


def check_register(request):
    """
    input - request -> {email(string), first_name(string), last_name(string),
                    password(string), password_again(string}
    output string: "" if no error, else an error string
    callers - check_register_ajax and register_ajax
    checks to make sure that the user has proper fields filled in
    """
    if request.method == "POST":
        rg = request.POST
    else:
        rg = request.GET
    error = ""
    email = rg["email"]
    name = rg["name"]
    password = rg["password"]
    location = rg["city"]

    # admin_emails = [address[1] for address in settings.ADMINS]

    if not utils.email_re.match(email):
        error += "Invalid email!\r\n"
    if User.objects.filter(email=email).exists():
        error += "Email already in use!\r\n"
    if Profile.objects.filter(email_normalized=utils.normalize_email(email)).exists():
        error += "Email previously registered! If your email is a gmail address did you perhaps already register? Check the periods and +'s in your email address.\r\n"
    if name == "":
        error += "You need a first/last name!\r\n"
    if password == "":
        error += "Please enter a password.\r\n"
    if not utils.only_roman_chars(password):
        error += "Please enter a password with only roman characters.\r\n"
    if location == "":
        error += "Please enter a location.\r\n"
    if rg["account_type"] == "":
        error += "You need to select an account type\r\n"
    return error


def check_register_ajax(request):
    """
    input - request -> {email(string), first_name(string), last_name(string),
                    password(string), password_again(string}
    output -> sends HttpResponse of the error to ajax call checkCorrectRegisterForm in registrationForm.js
    if all the forms are filled in correctly, error = "" else error is a real error message
    """
    return HttpResponse(check_register(request))


def login_ajax(request):
    "called from logIn in my_account.js. Redirects to splash"
    if request.method == "POST":
        url = request.POST.get("next", "/")
        email = request.POST["email"].lower()
        password = request.POST["password"]
        user = authenticate(email=email, password=password)

        if user:
            # set ip
            person = user.person
            if person.ipaddr is None:
                try:
                    ipaddr = utils.get_client_ip(request)
                except:
                    ipaddr = None
                else:
                    person.ipaddr = ipaddr

                person.last_login = datetime.datetime.now()
                person.save()

            # dont let the user login if they aren't verified!!!!
            if settings.REQUIRE_VERIFICATION_FOR_LOGIN and not person.verified:
                return HttpResponse("not_verified")

            login(request, user)

            if person.should_change_pass:  # type: ignore
                url = "/my-account/privacy/"
                return HttpResponse(url)

            if person.view != person.profile:  # type: ignore
                # make sure we are even IN a band (could have removed)
                mem = Membership.objects.filter(
                    group=person.view.organization, person=person  # type: ignore
                )
                if not mem or mem[0].admin is not True:
                    person.view = user.person.profile  # type: ignore
                    person.save()  # type: ignore

            try:
                private_key = hedera_utils.get_user_private_key(user, password)
            except hedera_utils.GetUserPrivateKeyError:
                private_key = None
            request.session[settings.PRIVATE_KEY_SESSION_KEY] = private_key

            if settings.TESTING or settings.DEBUG:
                hedera_utils.create_or_update_hedera_account(
                    request, password, private_key
                )
            else:
                t = threading.Thread(
                    target=hedera_utils.create_or_update_hedera_account,
                    args=[request, password, private_key],
                )
                t.setDaemon(True)
                t.start()

            if not request.user.person.passed_join_social:
                request.user.person.passed_join_social = True
                request.user.person.save()
                url = reverse("join_social")

            update_playlist_with_session(request)
            return HttpResponse(url)

        elif not User.objects.filter(email=email).exists():
            return HttpResponse("wrong_email")
        return HttpResponse("wrong_password")
    if request.GET.get("next"):
        return HttpResponse("/?next={}".format(request.GET.get("next")))
    return HttpResponse("/")


def log_out(request):
    """
    input - request (no special get/post parameters)
    caller - client (on pressing logout button)
    logs out the users (django auth system) and redirects to hearo one
    """
    logout(request)
    return HttpResponseRedirect("/")


@login_required
def deactivate_account(request):
    profile = request.user.person.profile
    profile.deactivate()
    return log_out(request)


def get_or_create_banner(profile):
    try:
        banner = profile.banner
    except Banner.DoesNotExist:
        banner = Banner(
            profile=profile,
            texture_chosen="sky",
            font="Permanent Marker",
            display_bar=True,
            crop_top=0,
            crop_bottom=40,
            crop_left=0,
            crop_right=240,
        )

        if profile.get_account_type() != "artist":
            banner.display_instrument = False

        # REVIEW: Why not display genre for venue? could be nice to look up
        # places which an artist could play in
        # if profile.organization.is_venue:
        #     banner.display_genre = False

        banner.save()
    return banner


def _create_user(first_name, last_name, email, password):
    "Creates and authenticates a new user with the registration forms"

    # Check if the first name has any capital letters. If not, capitalize the
    # first letter.

    pretty_first = ""
    pretty_last = ""
    first_letters = list(first_name)

    for letter in first_letters:
        if letter.isupper():
            pretty_first = first_name
            break

    if pretty_first != first_name:
        pretty_first = first_name.capitalize()

    # Check if the last name has any capital letters. If not, capitalize the
    # first letter.
    last_letters = list(last_name)
    for letter in last_letters:
        if letter.isupper():
            pretty_last = last_name
            break
    if pretty_last != last_name:
        pretty_last = last_name.capitalize()

    logger.debug("%s %s", pretty_first, pretty_last)

    user = User(email=email.lower(), first_name=pretty_first, last_name=pretty_last)
    user.username = user.email

    # Hash password
    user.set_password(password)
    user.save()
    user = authenticate(email=user.email, password=password)

    return user


def _create_profile_from_user(user, acctype):
    "Creates a regular profile from registration user"
    normalized_email = utils.normalize_email(user.email)
    profile = Profile(
        user=user,
        email_normalized=normalized_email,
        name="%s %s" % (user.first_name, user.last_name),
        default_download_format=DownloadFormat.MP3_320,
    )
    profile.short_name = utils.trim_name(profile.name)
    keyword = "_".join([user.first_name, user.last_name]).strip()
    profile.keyword = utils.ensure_unique_keyword(keyword, Profile)
    profile.save()
    Radio.objects.create(profile=profile)
    person = Person(
        user=user,
        view=profile,
        profile=profile,
        verification_key=UserManager().make_random_password(length=32),
    )

    person.save()

    orgo = Organization(profile=profile)
    orgo.set_type_and_save(acctype)
    orgo.add_member(profile.person, is_admin=True)

    get_or_create_banner(profile)

    send_verification(None, person)

    if settings.SERVER:
        the_hearo_team.send_intro(profile)

    if not settings.SERVER and not settings.DEBUG:
        try:
            mail_admins(
                "New user registered",
                "{} at https://{}{}".format(
                    user.email, settings.BASE_URL, profile.get_absolute_url()
                ),
            )
        except Exception:
            logger.exception("Error sending email regarding new user")

    return profile


def send_verification(request, person=None):
    # called from create_profile_from_user
    if person:
        p = person
        user = p.user
        id_ = p.id
        v_key = p.verification_key
        email = p.user.email
    else:
        # called from the not_verified html page
        email = request.POST["email"]
        try:
            user = User.objects.get(email=email)
            id_ = user.person.id
            v_key = user.person.verification_key
        except:
            return HttpResponse("This email is not tied to any account we can find!")
    utils.sendemail_template(
        [email],
        "email_notifications/send_verification.html",
        {"user": user, "id_": str(id_), "v_key": v_key,},
    )
    return HttpResponse("t")


def verify(request):
    """Called when the user follows the verification link that we sent them via
    email
    """
    v = request.GET.get("v")
    if v:
        _id, key = v.split("_")
        person = Person.objects.get(id=_id, verification_key=key)
        person.verified = True
        person.save()
        t = loader.get_template("accounts/verified.html")
        return utils.render_appropriately(
            request, t, {"saved": True, "name": person.profile.name}
        )
    logger.info("An error occurred verifying")
    t = loader.get_template("accounts/verified.html")
    return utils.render_appropriately(request, t, {"saved": False})


def not_verified(request):
    """Gets called when a user logs in for the first time without verifying
    their account
    """
    email = request.GET["email"]
    t = loader.get_template("accounts/not-verified.html")
    return utils.render_appropriately(request, t, {"email": email})


def _update_profile_genre(profile, genres):
    "Used by register ajax"

    if genres:
        genres = genres.split(",")
        genres = [i.strip().lower() for i in genres if i.strip()]
        if genres:
            old = set(profile.genres.all())
            new = set(Genre.objects.get_or_create(name=genre)[0] for genre in genres)
            add = new - old
            remove = old.difference(new)

            for genre in add:
                profile.genres.add(genre)

            for genre in remove:
                profile.genres.remove(genre)


def _update_profile_location(profile, loc):
    "Used by register ajax, sets the user location and country"
    if loc == "":
        profile.location = None
        profile.location_set = False
    else:
        try:
            # Geocode the string given
            g = geocoders.GoogleV3(api_key=settings.GOOGLE_MAPS_GEOCODING_API_KEY)
            place, (lat, lng) = list(g.geocode(loc, exactly_one=False))[0]  # type: ignore

            location_kwargs = dict(lat=lat, lng=lng, most_exact=place)
            locations = Location.objects.filter(**location_kwargs)
            if locations:
                location = locations[0]
            else:
                location = Location.objects.create(**location_kwargs)

            # Query the country this address is in
            try:
                country = get_country(loc)
                if country:
                    location.country = country["code"]
                    location.save()
            except Exception as e:
                logger.error(e)

            try:
                secondary = get_secondary(loc)
                if secondary:
                    location.secondary = secondary
                    location.save()
            except Exception as e:
                logger.error(e)

            profile.location = location
            profile.location_set = True
        except (GeocoderTimedOut, GeocoderQuotaExceeded, GeocoderServiceError) as e:
            logger.warning("GEOCODER ERROR: %s", e)


def _update_profile_instruments(musician, instruments):
    "Used by register ajax"
    if instruments:
        instruments = instruments.split(",")
        instruments = [i.strip().lower() for i in instruments if i.strip()]
        if instruments:
            old = set(musician.instruments.all())
            new = set(
                Instrument.objects.get_or_create(name=instrument)[0]
                for instrument in instruments
            )
            add = new - old
            remove = old.difference(new)

            for instrument in add:
                musician.instruments.add(instrument)

            for instrument in remove:
                musician.instruments.remove(instrument)


@transaction.atomic
def register_ajax(request):
    """
    input - request -> {email(string), first_name(string), last_name(string),
                    password(string), password_again(string), is_musician('t' or 'f')}
    caller - registerAjax in registrationForm.js
    output - HttpResponse(url to profile) gets sent to registerAjax
    creates a new user, person, and profile based on input. Also
    creates an accompanying musician object if the checkbox is checked

    request.POST returns a dict like this

    {u'account_type': [u'Artist'],
    u'csrfmiddlewaretoken': [u'7Gaf16LRzwJTlWFYHH9067zJQPrK3nN2'],
    u'dj': [u'f'],
    u'email': [u'test@testxx.com'],
    u'engineer': [u't'],
    u'genre': [u''],
    u'instruments': [u''],
    u'is_musician': [u'1'],
    u'join_band': [u'f'],
    u'city': [u'Nairobi, Kenya'],
    u'name': [u'test'],
    u'password': [u'asdfasdf'],
    u'producer': [u'f'],
    u'teacher': [u'f'],
    u'write_music': [u'f']}
    """
    error = check_register(request)

    if error:
        return HttpResponseBadRequest(error)

    rp = request.POST

    try:
        first_name, last_name = rp["name"].split(" ")
    except ValueError:
        first_name = rp["name"]
        last_name = ""

    email = rp["email"]

    try:
        validate_disposable_email(email)
    except ValidationError:
        return HttpResponseBadRequest("Invalid domain or disposable email")

    try:
        client = quickemailverification.Client(
            settings.QUICKEMAILVERIFICATION_API_KEY
        ).quickemailverification()
        response = client.verify(email)
        logger.info(response.body)
        if not (
            response.body["result"] == "valid"
            and response.body["disposable"] == "false"
            and response.body["safe_to_send"] == "true"
        ):
            return HttpResponseBadRequest("Invalid domain or disposable email")
    except Exception:
        pass

    password = rp["password"]

    user = _create_user(first_name, last_name, email, password)

    acctype = rp.get("account_type", "artist").lower()

    profile = _create_profile_from_user(user, acctype)
    person = profile.person

    if rp.get("city"):
        _update_profile_location(profile, rp["city"])
    if rp.get("genre"):
        _update_profile_genre(profile, rp.get("genre"))

    utils.assert_valid_acctype(acctype)

    if acctype == "artist":
        musician = Musician.objects.create(profileID=profile.keyword)
        _update_profile_instruments(musician, rp["instruments"])
        musician.join_band = rp["join_band"] == "t"
        musician.write_music = rp["write_music"] == "t"
        musician.teacher = rp["teacher"] == "t"
        musician.dj = rp["dj"] == "t"
        musician.save()

        person.musician = musician
        person.producer = rp["producer"] == "t"
        person.engineer = rp["engineer"] == "t"
        person.save()

        if rp["is_musician"] == "1":
            # Plays music
            person.is_musician = True
        else:
            # E.g. song writer
            person.is_musician = False
    elif acctype == "fan":
        person.is_musician = False

    person.save()
    profile.save()

    if settings.REQUIRE_VERIFICATION_FOR_LOGIN:
        url = reverse("not_verified") + "?email={}".format(user.email)  # type: ignore
    else:
        url = reverse("join_social")
        login(request, user)
        # TODO: if REQUIRE_VERIFICATION_FOR_LOGIN is false, we need to create the wallet here

    return HttpResponse(url)


@transaction.atomic
def create_page_ajax(request):
    """
    input - request -> {email(string), first_name(string), last_name(string),
                    password(string), password_again(string), is_musician('t' or 'f')}
    caller - registerAjax in registrationForm.js
    output - HttpResponse(url to profile) gets sent to registerAjax
    creates a new user, person, and profile based on input. Also
    creates an accompanying musician object if the checkbox is checked

    request.POST returns a dict like this

    {u'account_type': [u'Artist'],
    u'csrfmiddlewaretoken': [u'7Gaf16LRzwJTlWFYHH9067zJQPrK3nN2'],
    u'dj': [u'f'],
    u'email': [u'test@testxx.com'],
    u'engineer': [u't'],
    u'genre': [u''],
    u'instruments': [u''],
    u'is_musician': [u'1'],
    u'join_band': [u'f'],
    u'city': [u'Nairobi, Kenya'],
    u'name': [u'test'],
    u'password': [u'asdfasdf'],
    u'producer': [u'f'],
    u'teacher': [u'f'],
    u'write_music': [u'f']}
    """
    if request.method != "POST":
        return HttpResponseBadRequest()

    person = request.user.person.view

    rp = request.POST

    acctype = rp.get("account_type", "artist").lower()

    profile = form_organization(request.user.profile, rp["name"], acctype)

    if acctype == "artist":
        musician = Musician.objects.create(profileID=profile.keyword)
        _update_profile_instruments(musician, rp["instruments"])
        musician.join_band = rp["join_band"] == "t"
        musician.write_music = rp["write_music"] == "t"
        musician.teacher = rp["teacher"] == "t"
        musician.dj = rp["dj"] == "t"
        musician.save()

        person.musician = musician
        person.producer = rp["producer"] == "t"
        person.engineer = rp["engineer"] == "t"
        person.save()

        if rp["is_musician"] == "1":
            # Plays music
            person.is_musician = True
        else:
            # E.g. song writer
            person.is_musician = False

    _update_profile_location(profile, rp["city"])
    _update_profile_genre(profile, rp.get("genre"))

    profile.biography = rp.get("biography")
    profile.influences = rp.get("influences")
    profile.experience = rp.get("experience")
    profile.goals = rp.get("goals")

    person.view = profile

    person.save()
    profile.save()

    return JsonResponse({"profile_id": profile.id, "profile_keyword": profile.keyword})


def switch_account(request, accountid):
    "Returns a dict of session_info"
    person = request.user.person
    profile = Profile.objects.get(id=accountid)
    if profile in person.get_accounts():
        person.view = profile
        person.save()
    return HttpResponse("ok")


def about(request):
    t = loader.get_template("about.html")
    return utils.render_appropriately(request, t, {"pageclass": "about",})


def signup(request):
    t = loader.get_template("landing/index.html")
    return utils.render_appropriately(request, t, {"pageclass": "signup",})


def index(request):
    """Account status updates"""
    user = request.user
    fan_feeds = None
    if user.is_authenticated:
        t = loader.get_template("accounts/index.html")
        fan_feeds = Feed.decorated_fan_feed_for(user, request)
        # fan_feeds = add_raw_reviews(fan_feeds)

    else:
        return HttpResponseRedirect(reverse("join_index"))

    # Featured
    artists = Profile.objects.filter(splash_featured=True)
    albums = Album.objects.filter(splash_featured=True)
    songs = Song.objects.filter(splash_featured=True)

    # TEMPORARY HACK SORRY - Artur
    default_img = DEF_MUSICLISTING_IMG

    rendered_featured_artists = "".join(
        [
            loader.render_to_string(
                "common/music.listing.html",
                {
                    "title": artist.name,
                    "subtitle": artist.location or "",
                    "image": artist.get_music_listing_img() or default_img,
                    "profileurl": artist.get_absolute_url(),
                    "entity_type": "artist",
                    "play_button_type": "song",
                    "play_button_id": artist.get_music_listing_songid(),
                    "entity": artist,
                    "view": utils.get_profile(request.user),
                },
            )
            for artist in artists
        ]
    )

    rendered_featured_albums = "".join(
        [
            loader.render_to_string(
                "common/music.listing.html",
                {
                    "title": album.title,
                    "subtitle": "by %s" % album.profile.name,
                    "image": album.small_cover or default_img,
                    "profileurl": "/profile/%s" % album.profile.keyword,
                    "entity_type": "album",
                    "play_button_type": "album",
                    "play_button_id": album.id,
                    "entity": album,
                    "view": utils.get_profile(request.user),
                },
            )
            for album in albums
        ]
    )

    rendered_featured_songs = "".join(
        [
            loader.render_to_string(
                "common/music.listing.html",
                {
                    "title": song.title,
                    "subtitle": "by %s" % song.profile.name,
                    "image": song.profile.get_music_listing_img() or default_img,
                    "profileurl": "/profile/%s" % song.profile.keyword,
                    "entity_type": "song",
                    "play_button_type": "song",
                    "play_button_id": song.id,
                    "entity": song,
                    "view": utils.get_profile(request.user),
                },
            )
            for song in songs
        ]
    )

    return utils.render_appropriately(
        request,
        t,
        {
            "contentclass": "home",
            "featured_artists": rendered_featured_artists,
            "featured_albums": rendered_featured_albums,
            "featured_songs": rendered_featured_songs,
            "feeds": fan_feeds,
        },
    )


def join_index(request):
    "Email join register screen"
    email = request.GET.get("email")
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("join_social"))
    t = loader.get_template("accounts/join/index.html")
    return utils.render_appropriately(
        request, t, {"contentclass": "join signup", "email": email, "progress": 1,}
    )


def join_social(request):
    "Social join register screen"
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("join_index"))
    t = loader.get_template("accounts/join/social.html")
    return utils.render_appropriately(
        request, t, {"contentclass": "join social", "progress": 2}
    )


def join_welcome(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("join_index"))
    t = loader.get_template("accounts/join/welcome.html")
    return utils.render_appropriately(
        request, t, {"contentclass": "join welcome one", "progress": 3}
    )


def get_reviews(request):
    # Pre: pass in a model name (str) and ID (int) thru AJAX
    # Post: get back the reviews and if OP reviewed this entity: [ [ {review1},
    # {review2} ], { did op review this?: bool } ]
    model, qid = request.GET["model"], request.GET["id"]
    if request.user.is_authenticated:
        reviewer = request.user.person.view
        logged_in = True
    else:
        reviewer = False
        logged_in = False

    review = None

    if model == "song":
        song = Song.objects.get(id=qid)
        reviews = song.get_reviews()
        avg_rating = song.avg_review_rating()
        try:
            review = Review.objects.get(song=song, reviewer=reviewer)
        except Review.DoesNotExist:
            pass
        except Review.MultipleObjectsReturned:
            review = Review.objects.filter(song=song, reviewer=reviewer)[0]
            user_reviews = Review.objects.filter(song=song, reviewer=reviewer)[1:]
            for obj in user_reviews:
                obj.delete()
        already_reviewed = bool(reviewer and review)
        metadata = {"name": song.title, "artist": song.profile.jsonify(request)}
    elif model == "album":
        album = Album.objects.get(id=qid)
        reviews = album.get_reviews()
        avg_rating = album.avg_review_rating()
        try:
            review = Review.objects.get(album=album, reviewer=reviewer)
        except Review.DoesNotExist:
            pass
        except Review.MultipleObjectsReturned:
            review = Review.objects.filter(album=album, reviewer=reviewer)[0]
            user_reviews = Review.objects.filter(album=album, reviewer=reviewer)[1:]
            for obj in user_reviews:
                obj.delete()
        already_reviewed = bool(reviewer and review)
        metadata = {"name": album.title, "artist": album.profile.jsonify(request)}
    elif model == "profile":
        profile = Profile.objects.get(id=qid)
        reviews = profile.get_reviews()
        avg_rating = profile.avg_review_rating()

        try:
            review = Review.objects.get(profile=profile, reviewer=reviewer)
        except Review.DoesNotExist:
            pass
        except Review.MultipleObjectsReturned:
            review = Review.objects.filter(profile=profile, reviewer=reviewer)[0]
            user_reviews = Review.objects.filter(profile=profile, reviewer=reviewer)[1:]
            for obj in user_reviews:
                obj.delete()
        already_reviewed = bool(reviewer and review)
        metadata = {"name": profile.name, "artist": profile.jsonify(request)}
    else:
        return HttpResponse(status=500)

    userinfo = {"user_reviewed": already_reviewed, "logged_in": logged_in}
    if review:
        userinfo["review"] = jsonify_review(request, review)  # type: ignore

    reviews_list = [jsonify_review(request, r) for r in reviews]
    reviews_list.reverse()
    return JsonResponse(
        {
            "reviews_list": reviews_list,
            "userinfo": userinfo,
            "metadata": metadata,
            "avg_rating": avg_rating,
        },
        safe=False,
    )


@utils.ajax_login_required
def post_review_ajax(request):
    model = request.POST["model"]
    qid = request.POST["qid"]
    review = request.POST["review"]
    stars = int(request.POST["stars"])
    view = request.user.person.view

    if model == "song":
        song = Song.objects.get(id=qid)
        existent = Review.objects.filter(reviewer=view, song=song)
        if existent.exists():
            existent = existent[0]
            existent.review = review
            existent.stars = stars
            existent.save()
        else:
            existent = Review(reviewer=view, review=review, song=song, stars=stars)
            existent.save()

    elif model == "album":
        album = Album.objects.get(id=qid)
        existent = Review.objects.filter(reviewer=view, album=album)
        if existent.exists():
            existent = existent[0]
            existent.review = review
            existent.stars = stars
            existent.save()
        else:
            existent = Review(reviewer=view, review=review, album=album, stars=stars)
            existent.save()

    elif model == "profile":
        profile = Profile.objects.get(id=qid)
        existent = Review.objects.filter(reviewer=view, profile=profile)
        if existent.exists():
            existent = existent[0]
            existent.review = review
            existent.stars = stars
            existent.save()
        else:
            existent = Review(
                reviewer=view, review=review, profile=profile, stars=stars
            )
            existent.save()
    else:
        return HttpResponse(status=500)
    return JsonResponse(jsonify_review(request, existent))


def jsonify_review(request, r):
    # Render the HTML display of the review for the reviews sidebar
    t = loader.get_template("common/review.html")
    html = utils.render_appropriately(
        request,
        t,
        {
            "review_content": r.review,
            "reviewer_href": "/profile/%s" % r.reviewer.keyword,
            "reviewer": r.reviewer,
            "stars": r.stars,
        },
    ).content

    # Return the html along with the raw data
    return {
        "review": r.review,
        "reviewer": r.reviewer.jsonify(request),
        "date": r.review_date.strftime("%a, %b %d %I:%M %p"),
        "html": html.decode("utf-8"),
        "stars": r.stars,
        "avg": r.owner().avg_review_rating(),
    }


@utils.ajax_login_required
def delete_post_ajax(request):
    profile_ = request.user.person.view
    post_id = request.POST["post_id"]
    try:
        StatusUpdate.objects.get(
            Q(id=int(post_id)) & (Q(profile=profile_) | Q(profile_commenter=profile_))
        ).delete()
        return HttpResponse(status=200)
    except:
        return HttpResponse(status=500)


@utils.ajax_login_required
def post_status_ajax(request):
    view = request.user.person.view
    if request.method == "POST":
        rp = request.POST
        profile_get = Profile.objects.get(id=rp["profile_id"])
        if profile_get == view:
            # Post to own profile
            status_update = StatusUpdate.objects.create(
                profile=view, status=rp["status_update"]
            )
        else:
            # Post message to other profile
            status_update = StatusUpdate.objects.create(
                profile=profile_get, status=rp["status_update"], profile_commenter=view
            )

        # use the template tags to render the ajax success
        return render_to_response(
            "common/status-post.html", {"update": status_update, "view": view}
        )
    return HttpResponseBadRequest()


def review_artwork(request, elem_type, elem_id):
    art = "/public/images/defaults/review.png"
    if elem_type == "profile":
        profile = Profile.objects.get(id=elem_id)
        if profile.primary_photo is not None:
            art = "/%s" % profile.primary_photo.square_file.url
    elif elem_type == "song":
        song = Song.objects.get(id=elem_id)
        if song.album:
            try:
                art = "/%s" % song.album.small_cover.url
            except ValueError:
                pass
        elif song.profile.primary_photo is not None:
            art = "/%s" % song.profile.primary_photo.square_file.url
    elif elem_type == "album":
        album = Album.objects.get(id=elem_id)
        try:
            art = "/%s" % album.small_cover.url
        except ValueError:
            pass
    elif elem_id == "album":
        pass
    return HttpResponseRedirect(art)


@utils.ajax_login_required
def get_profile_progress_ajax(request):
    view = request.user.person.view
    return JsonResponse(view.get_profile_progress(), safe=False)


def profile(request, slug, section):
    try:
        profile_get = Profile.objects.get(keyword=slug)
    except Profile.DoesNotExist:
        raise Http404()

    user = request.user
    person = profile_get.person

    if user.is_anonymous:
        own = False
    else:
        own = request.user.person.view.keyword == profile_get.keyword

    if profile_get.profile_private and not own:
        raise Http404()

    t = loader.get_template("accounts/profile.html")
    songs = Song.objects.filter(profile=profile_get, deleted=False).order_by(
        "track_num"
    )

    albums = (
        Album.objects.all()
        .filter(profile=profile_get, deleted=False)
        .order_by("-year_released", "-upload_date")
    )

    # Only use albums with playable
    albums = [a for a in albums if a.songs.count() > 0]

    releases_empty = (
        songs.filter(online=True, processing=False).count() + len(albums)
    ) == 0

    prof_updates = (
        profile_get.updates.all().order_by("-update_date").select_related()[:15]
    )

    all_faned = profile_get.get_faned()
    all_faned_profiles = [f.fanee for f in all_faned]
    fan_updates = (
        StatusUpdate.objects.exclude(profile=profile_get)
        .filter(profile__in=all_faned_profiles)
        .only("id")
        .order_by("-update_date")[:20]
    )

    fans = (
        profile_get.get_fans()
        .only("keyword", "name", "primary_photo")
        .prefetch_related("primary_photo")
    )

    events = get_profile_events(profile_get)

    groups = []

    if profile_get.is_person():
        # true if view is person
        groups = [
            mem.group.profile
            for mem in Membership.objects.filter(person=profile_get.person)
        ]
    else:
        # organization
        pass

    members = [
        mem.person.profile
        for mem in Membership.objects.filter(group=profile_get.organization)
        if mem.person.profile != profile_get
    ]

    # Bottom left module info - create a list of key, value tuples (strings)
    info = []

    # Bottom left module badges - create a list of phrases (strings)
    badges = profile_get.get_badges()

    # Bio
    bio = None
    if profile_get.biography:
        bio = profile_get.biography

    # Location
    if profile_get.location_set:
        info.append(("from", [profile_get.location.most_exact]))

    if profile_get.get_account_type() not in ["fan"]:
        # Genres
        genres = profile_get.genres.all()
        if genres.count() > 0:
            info.append(
                (
                    "genre%s " % ("s" if genres.count() > 1 else ""),
                    [genre.slug for genre in genres],
                )
            )

    if profile_get.get_account_type() == "artist":
        # Check if profile is an artist and has a musician record
        try:
            instruments = profile_get.person.musician.instruments.all()
        except:
            instruments = None
        else:
            if instruments.count() > 0:
                info.append(
                    (
                        "play%s " % ("s" if instruments.count() > 1 else ""),
                        [inst.slug for inst in instruments],
                    )
                )

    fandlib = get_fandlib(profile_get)
    fandlib_empty = True

    for key, val in list(fandlib.items()):
        if len(val) != 0:
            fandlib_empty = False
        break

    if not profile_get.profile_layout_settings:
        # If the profile layout settings are undefined,
        # create them and continue.
        profile_get.profile_layout_settings = (
            '{"fansHeight": "610", "updatesHeight": "425"}'
        )
        profile_get.save()

    layout_settings = json.loads(profile_get.profile_layout_settings)

    updates_height = int(layout_settings["updatesHeight"])
    fans_height = int(layout_settings["fansHeight"])

    if profile_get.is_orgo():
        if profile_get.organization.is_venue:
            shows = Event.objects.filter(venue=profile_get.organization.venue)
        else:
            shows = list(Event.objects.filter(artists=profile_get)) + [
                s.fanned_event for s in FanEvent.objects.filter(fanner=profile_get)
            ]
    else:
        shows = [s.fanned_event for s in FanEvent.objects.filter(fanner=profile_get)]

    reviews = Review.objects.filter(profile=profile_get)

    user_feed = Feed.decorated_user_feed_for(profile_get, request)

    # user_feed = add_raw_reviews(user_feed)

    response_dict = {
        "user": request.user,
        "profile": profile_get,
        "fans": fans,
        "albums": albums,
        "songs": songs,
        "singles": profile_get.get_non_album_songs(),
        "releases_empty": releases_empty,
        "prof_updates": prof_updates,
        "fan_updates": fan_updates,
        "user_feed": user_feed,
        "videos": Video.objects.filter(profile=profile_get),
        "events": events,
        "shows": shows,
        "info": info,
        "exeperience": profile_get.experience,
        "goals": profile_get.goals,
        "influences": profile_get.influences,
        "reviews": reviews,
        "bio": bio,
        "nobio": profile_get.biography == "",
        "badges": badges,
        # Fandlib, and if fandlib is empty
        "fandlib": fandlib,
        "fandlib_empty": fandlib_empty,
        "library_show": "songs",
        "updatesHeightSetting": updates_height,
        "fansHeightSetting": fans_height,
        "linked_album_id": request.GET["albumid"] if "albumid" in request.GET else "",
        "radio_available": radio_available(profile_get.id),
        "own": own,
        "absloute_url": request.build_absolute_uri(),
        "contentclass": "profile",
        "members": members,
    }

    if not section:
        if profile_get.is_orgo():
            section = "releases"
        elif profile_get.person.is_musician:
            if fandlib_empty and releases_empty:
                section = "releases"
            elif (not fandlib_empty) and (not releases_empty):
                section = "releases"
            elif fandlib_empty:
                section = "releases"
            else:
                section = "library"
                for key, val in list(fandlib.items()):
                    if len(val) > 0:
                        response_dict["library_show"] = key
                        break
        else:
            section = "library"

    response_dict["section"] = section

    if "switchid" in request.GET:
        if not user.is_anonymous:
            # / can sometimes get in
            switch_account(request, request.GET["switchid"].strip("/"))

    if profile_get.is_person():
        response_dict.update({"groups": groups, "person": person})
        return utils.render_appropriately(request, t, response_dict)
    return utils.render_appropriately(request, t, response_dict)


@utils.ajax_login_required
def adjust_profile_layout_setting(request):
    p = request.POST
    profile = request.user.person.view

    val = p["val"]
    which = p["which"]

    if which == "updatesHeight":
        profile.set_layout_attr("updatesHeight", val)
    elif which == "fansHeight":
        profile.set_layout_attr("fansHeight", val)

    return HttpResponse(status=200)


def get_profile_events(profile_get):
    now = timezone.now()
    fan_events = (
        profile_get.fan_events.all()
        .filter(fanned_event__starts__gte=now)
        .exclude(fanned_event__profile=profile_get)
    )
    fanned_events = [event.fanned_event for event in fan_events]

    my_events = Event.objects.filter(profile=profile_get).exclude()

    # events im playing at
    playing_events = profile_get.shows.all()
    # remove duplicates
    a = set(itertools.chain(my_events, fanned_events, playing_events))
    events = sorted(a, key=lambda event: event.starts)
    return events


@utils.ajax_login_required
def get_profile_events_ajax(request):
    "gets called when you create an event via the profile"
    profile = request.user.person.view
    events = get_profile_events(profile)

    return HttpResponse(
        json.dumps([e.jsonify(request) for e in events], cls=DjangoJSONEncoder)
    )


@utils.ajax_login_required
def delete_event_ajax(request):
    _id = request.POST["id"]
    event = Event.objects.get(id=_id)
    if event.profile == request.user.person.view:  # DONT TRUST THE WEB
        event.delete()
        return HttpResponse("")
    return HttpResponseBadRequest()


def get_fandlib(profile):
    songs = SongFanEvent.objects.select_related().filter(
        faner=profile, faned_song__deleted=False
    )
    albums = AlbumFanEvent.objects.select_related().filter(
        faner=profile, faned_album__deleted=False
    )
    bands = Band.objects.select_related().filter(organization__profile__fans=profile)
    venues = Venue.objects.select_related().filter(organization__profile__fans=profile)
    labels = Label.objects.select_related().filter(organization__profile__fans=profile)
    musicians = Profile.objects.select_related().filter(
        person__is_musician=True, fans=profile
    )
    fans = Profile.objects.select_related().filter(
        person__is_musician=False, fans=profile
    )
    return {
        "songs": songs,
        "albums": albums,
        "bands": bands,
        "venues": venues,
        "labels": labels,
        "musicians": musicians,
        "fans": fans,
    }


# This runs onLoad for each profile. it sets their DTJ status and loads their
# bands (or members if they are a band or venue or w/e)
def profile_info_ajax(request, slug):
    profile = Profile.objects.get(keyword=slug)
    info = {"onair": profile.on_air, "dtj": profile.down_to_jam}
    if profile.is_person():
        target = profile.person
        if target.organizations:
            info["bands"] = [org.profile.jsonify(request) for org in target.get_bands()]
    elif profile.is_orgo():
        target = profile.organization
        if target.members:
            info["members"] = [p.profile.jsonify(request) for p in target.members.all()]
    return JsonResponse([info], safe=False)


def form_organization(profile, name, acctype):
    org_prof = Profile.objects.create(
        name=name,
        short_name=utils.trim_name(name),
        default_download_format=DownloadFormat.MP3_320,
        keyword=utils.ensure_unique_keyword(
            re.sub(r"\s", "_", name).replace("'", ""), Profile
        ),
    )

    utils.assert_valid_acctype(acctype)

    orgo = Organization(profile=org_prof)
    orgo.set_type_and_save(acctype)
    get_or_create_banner(org_prof)
    orgo.add_member(profile.person, is_admin=True)
    Radio.objects.create(profile=org_prof)
    return org_prof


@login_required
def account_profile_ajax(request):
    """
    input: request -> {biography,influences,experience,goals}
    if is musician also {join_band,write_music,instruments,genre}
    """
    if request.method != "POST":
        return HttpResponseBadRequest()

    view = request.user.person.view
    person = request.user.person

    rp = request.POST

    _update_profile_location(view, rp.get("city"))
    _update_profile_genre(view, rp.get("genre"))

    acctype = rp["account_type"].lower()

    utils.assert_valid_acctype(acctype)

    if acctype == "artist":
        org = view.organization
        org.set_type_and_save("artist")

        musician = person.musician
        if not musician:
            musician = Musician.objects.create(profileID=view.keyword)
            person.musician = musician
            person.save()

        _update_profile_instruments(musician, rp["instruments"])

        musician.join_band = rp["join_band"] == "t"
        musician.write_music = rp["write_music"] == "t"
        musician.teacher = rp["teacher"] == "t"
        musician.dj = rp["dj"] == "t"
        musician.save()

        person.musician = musician
        person.producer = rp["producer"] == "t"
        person.engineer = rp["engineer"] == "t"
        person.save()

        if rp["is_musician"] == "t":
            # Plays music
            person.is_musician = True
        else:
            # E.g. song writer
            person.is_musician = False

    elif acctype == "fan":
        org = view.organization
        org.set_type_and_save("fan")

        person.is_musician = False
        if person.musician:
            person.musician.delete()
            person.musician = None

    else:
        # Apply to bands and venues
        org = view.organization
        org.set_type_and_save(acctype)

    view.biography = rp.get("biography")
    view.influences = rp.get("influences")
    view.experience = rp.get("experience")
    view.goals = rp.get("goals")

    person.save()
    view.save()

    return HttpResponse("saved")


@login_required
def my_account_profile(request):
    "serves the my account profile tab"

    t = loader.get_template("accounts/my-account/profile.html")
    person = request.user.person
    view = person.view
    org = view.organization

    members, admins = org.get_membership()
    my_genres = ", ".join([g.name for g in view.genres.all()])
    if my_genres:
        my_genres += ", "

    context = {
        "instruments": Instrument.objects.all(),
        "genres": Genre.objects.all(),
        "my_genres": my_genres,
        "contentclass": "dashboard profile",
        "account_type": view.get_account_type(),
        "members": members,
        "admins": admins,
        "profile": request.user.profile,
    }
    try:
        i_list = ", ".join([i.name for i in person.musician.instruments.all()])
        if i_list:
            # add comma if there are elements already
            i_list += ", "
        context["my_instruments"] = i_list
    except:
        pass
    return utils.render_appropriately(request, t, context)


@login_required
def my_account_music(request):
    "music tab"
    t = loader.get_template("accounts/my-account/music.html")
    view = request.user.person.view

    albums = Album.objects.filter(profile=view, deleted=False).order_by("-id")

    non_album = view.get_non_album_songs().order_by("track_num", "upload_date")

    has_music = Song.objects.filter(profile=view, deleted=False).exists()

    context = {
        "person": view,
        "albums": albums,
        "non_album": non_album,
        "countries": list(COUNTRIES.values()),
        "has_music": has_music,
        "signed_agreement": view.signed_artist_agreement,
        "contentclass": "dashboard music",
    }
    return utils.render_appropriately(request, t, context)


@login_required
def my_account_downloads(request):
    "serves the my account profile downloads template"
    t = loader.get_template("accounts/my-account/downloads.html")
    downloadCharges = DownloadCharge.objects.filter(profile=request.user.profile)
    return utils.render_appropriately(
        request,
        t,
        {
            "downloads": downloadCharges,
            "DOWNLOAD_FORMATS": DownloadFormat.CHOICES,
            "contentclass": "dashboard downloads",
        },
    )


def change_default_download(request):
    if request.method == "POST":
        view = request.user.person.view
        view.default_download_format = request.POST["download_type"]
        view.save()
        return HttpResponse("saved")
    return HttpResponse("error")


def delete_page_ajax(request):
    # Doesn't actually delete the page
    # removes members from a page, once all members have been removed the page
    # can be deleted
    person = request.user.person
    if request.method == "POST":
        _id = request.POST["id"]
        org = Organization.objects.get(id=_id)
        org.remove_member(person)
        # Check membership count to see if we can disable the profile
        if org.members.count() == 0:
            profile = org.profile
            profile.deactivate()
        return HttpResponse(org.profile.name)
    return HttpResponseBadRequest()


@transaction.atomic
def join_page_ajax(request):
    person = request.user.person
    if request.method == "POST":
        _id = request.POST["id"]
        org = Organization.objects.get(id=_id)
        org.add_member(person, is_admin=False)
        t = loader.get_template("accounts/my-account/_pages.html")
        c = dict(
            groups=[
                mem.group
                for mem in Membership.objects.filter(person=person).order_by(
                    "date_joined"
                )
            ],
            view=person,
            profile=request.user.profile,
            user=request.user,
        )
        ret = dict(page_snippet=t.render(c))
        return utils.JSON(ret)
    return HttpResponseBadRequest()


@login_required
def get_membership_snippet(request):
    if request.method == "POST":
        _id = request.POST["id"]
        org = Organization.objects.get(id=_id)
        view = org.profile
        members, admins = org.get_membership()
        t = loader.get_template("accounts/my-account/_membership.html")
        c = dict(
            org=org,
            view=view,
            members=members,
            admins=admins,
            profile=request.user.profile,
        )
        ret = dict(page_snippet=t.render(c))
        return utils.JSON(ret)
    return HttpResponseBadRequest()


@login_required
def my_account_pages(request):
    """
    Show pages the current logged in user has access to.

    Can only be displayed for 'persons'.
    """
    person = request.user.person
    profile = request.user.profile
    t = loader.get_template("accounts/my-account/pages.html")
    groups = person.organizations.all()
    membership_groups = [
        mem.group
        for mem in Membership.objects.filter(person=person).order_by("date_joined")
    ]
    pending_groups = [group for group in groups if group not in membership_groups]
    return utils.render_appropriately(
        request,
        t,
        {
            "pending_groups": pending_groups,
            "groups": membership_groups,
            "profile": profile,
            "contentclass": "dashboard pages",
        },
    )


def make_admin_ajax(request):
    "Makes an existing member an admin"
    profileid = int(request.POST["profileid"])
    groupid = int(request.POST["groupid"])
    org = Organization.objects.get(pk=groupid)
    if org.user_is_admin_or_profile_owner(request.user.profile):
        mem = Membership.objects.get(group=org, person__profile__id=profileid)
        mem.admin = True
        mem.save()
        return HttpResponse(profileid)
    return HttpResponseBadRequest("You must be a admin to make this change")


def delete_admin_ajax(request):
    "Changes a member from admin to regular member"
    profileid = int(request.POST["profileid"])
    groupid = int(request.POST["groupid"])
    org = Organization.objects.get(pk=groupid)
    if org.user_is_admin_or_profile_owner(request.user.profile):
        mem = Membership.objects.get(group=org, person__profile__id=profileid)
        mem.admin = False
        mem.save()
        return HttpResponse(profileid)
    return HttpResponseBadRequest("You must be a admin to make this change")


def delete_member_ajax(request):
    "Removes a member from a group"
    profileid = int(request.POST["profileid"])
    groupid = int(request.POST["groupid"])
    org = Organization.objects.get(pk=groupid)
    prof = Profile.objects.get(pk=profileid)
    if (
        org.user_is_admin_or_profile_owner(request.user.profile)
        or request.user.profile.id == prof.id
    ):
        org.remove_member(prof.person)
        return HttpResponse(profileid)
    return HttpResponseBadRequest("You must be a admin to make this change")


def update_membership_split_ajax(request):
    percentage_split = float(request.POST["percentage_split"])
    personid = int(request.POST["personid"])
    groupid = int(request.POST["groupid"])
    org = Organization.objects.get(pk=groupid)
    person = Person.objects.get(pk=personid)
    if org.user_is_admin_or_profile_owner(request.user.profile):
        org.update_share_split(person, percentage_split)
        return HttpResponse(person.id)
    return HttpResponseBadRequest("You must be a admin to make this change")


def send_request_ajax(request):
    invite_id = request.POST["invitee"]
    invitee = Profile.objects.get(id=invite_id)

    orgid = request.POST.get("groupid", request.user.person.view.organization.id)
    org = Organization.objects.get(pk=int(orgid))

    prof = org.profile
    message = "You have been invited to {}! Confirm invitation on the groups page of your dashboard! https://{}/my-account/pages/".format(
        prof.name, settings.BASE_URL
    )

    person = invitee.person

    if not Membership.objects.filter(person=person, group=org).exists():
        org.make_pending_member(person)
        Message.objects.create(
            to_profile=invitee,
            from_profile=prof,
            body=message,
            subject="you're invited!",
        )
        utils.sendemail_template(
            [person.user.email],
            "email_notifications/send_invitation.html",
            {"message": message, "prof": prof},
        )
        return utils.JSON([person.profile.jsonify(request)])
    return HttpResponseBadRequest()


def change_password_ajax(request):
    user = request.user
    errors = []
    changed_pass = False
    if request.method == "POST":
        curpass = request.POST["curpass"]
        password = request.POST["pass"]
        password_again = request.POST["pass2"]
        if user.check_password(curpass):
            if password == password_again:
                private_key = None
                wallet = user.wallet
                try:
                    # We wrap this around a try except block since we want the
                    # user to be able to change their password regardless of weither the
                    # wallet can be unlocked
                    # E.g. if the password was reset, the password wont unlock the key

                    # Decrypt Hedera private key using original pass
                    if wallet.hedera_private_key:
                        encrypted_message = pgpy.PGPMessage.from_blob(
                            wallet.hedera_private_key
                        )

                        old_key = pgpy.PGPKey()
                        old_key.parse(wallet.openpgp_key)

                        with old_key.unlock(curpass) as unlocked_key:
                            decrypted_message = unlocked_key.decrypt(encrypted_message)
                            if len(decrypted_message.message) == 96:
                                # We have the key
                                private_key = decrypted_message.message
                except Exception as e:
                    logger.exception("Failed to decrypt key on password change: %s", e)

                if private_key is None:
                    failed_to_unlock_hedera_private_key = True
                else:
                    failed_to_unlock_hedera_private_key = False
                    # Create new openpgp key
                    full_name = "{} {}".format(user.first_name, user.last_name)
                    if wallet.hedera_private_key:
                        new_key = openpgp_utils.create_key(full_name, user.email)
                        openpgp_utils.lock(new_key, password)

                        # Reencrypt using new pass
                        message = pgpy.PGPMessage.new(private_key)
                        encrypted_private_key = new_key.pubkey.encrypt(message)
                        wallet.openpgp_key = str(new_key)
                        wallet.hedera_private_key = encrypted_private_key
                        wallet.save()

                # Set new user password
                changed_pass = True
                user.set_password(password)
                user.person.should_change_pass = False
                user.person.save()
                user.save()

                # - store everything
                # - send the user an email
                utils.sendemail_template(
                    [user.email],
                    "email_notifications/send_password_changed_email.html",
                    {
                        "user": user,
                        "new_password": password,
                        "failed_to_unlock_hedera_private_key": failed_to_unlock_hedera_private_key,
                    },
                )
            else:
                errors += ["password_mismatch"]

        elif password or password_again:
            # error message
            errors += ["invalid_current_password"]

    return JsonResponse([errors, changed_pass], safe=False)


def user_settings_ajax(request):
    user = request.user
    error = []
    if request.method == "POST":
        rp = request.POST
        new_name = rp["name"]
        if new_name:
            user.person.view.name = new_name
            user.person.view.short_name = utils.trim_name(new_name)

        view = request.user.person.view
        view.fanmail_private = rp["fanmail_privacy"] == "Private"
        # view.downloads_private = rp['downloads_privacy'] == 'Private'
        view.profile_private = rp["profile_privacy"] == "Private"

        view.save()

        user_settings = view.settings

        user_settings.receive_weekly_digest = rp["receive_weekly_digest"] == "t"
        user_settings.receive_monthly_digest = rp["receive_monthly_digest"] == "t"
        user_settings.notify_fan_mail = rp["notify_fan_mail"] == "t"
        user_settings.notify_review = rp["notify_review"] == "t"
        # user_settings.notify_tip = rp['notify_tip'] == 't'
        # user_settings.notify_downloads = rp['notify_downloads'] == 't'
        user_settings.notify_fan = rp["notify_fan"] == "t"
        user_settings.notify_fan_threshold = rp["notify_fan_threshold"]
        user_settings.notify_play = rp["notify_play"] == "t"
        user_settings.notify_play_threshold = rp["notify_play_threshold"]
        # user_settings.notify_events = rp['notify_events'] == 't'

        user_settings.save()
        user.save()

    return JsonResponse([error], safe=False)


@login_required
def user_settings(request):
    t = loader.get_template("accounts/my-account/user_settings.html")
    view = request.user.person.view
    should_change_pass = request.user.person.should_change_pass
    privacy_options = [
        ("fanmail", view.fanmail_private),
        # ('downloads', view.downloads_private),
        ("profile", view.profile_private),
    ]

    changes_via_url = handle_unsubscribes(request)

    return utils.render_appropriately(
        request,
        t,
        {
            "privacy_options": privacy_options,
            "should_change_pass": should_change_pass,
            "contentclass": "dashboard privacy",
            "changes_via_url": changes_via_url,
        },
    )


def handle_unsubscribes(request):
    user = request.user
    if not user:
        return False
    profile = request.user.profile
    if not profile:
        return False
    settings = profile.settings
    if not settings:
        return False

    attrs = (
        "receive_weekly_digest",
        "receive_monthly_digest",
        "notify_fan_mail",
        "notify_review",
        "notify_tip",
        "notify_downloads",
        "notify_fan",
        "notify_play",
        "notify_events",
    )

    unsubscribe_all = False

    if request.GET.get("unsubscribe_all"):
        unsubscribe_all = True

    for attr in attrs:
        value = request.GET.get(attr, False)
        if unsubscribe_all:
            setattr(settings, attr, False)
        if value == "false":
            setattr(settings, attr, False)
        elif value == "true":
            setattr(settings, attr, True)

        if value:
            settings.save()
            return "Your email notification settings have been updated."

    settings.save()

    if unsubscribe_all:
        return "You have disabled email notifications."

    return False


def my_account_private_location_ajax(request):
    """Called from changePrivateLocation in my_account.js when user tries to
    save

    """
    profile = request.user.person.view
    validate = validate_address(request)
    if not validate:
        logger.error("Could not validate address", exc_info=True)
        return HttpResponse(status=500)

    if request.method == "POST" and validate:
        profile.p_address1 = request.POST["address1"]
        profile.p_address2 = request.POST["address2"]
        profile.p_city = request.POST["city"]
        profile.p_state = request.POST.get("state")
        profile.p_zip = request.POST.get("zip")

        country = request.POST["country"]
        if country not in list(COUNTRIES.values()):
            logger.error("INVALID COUNTRY %s", country)
            return HttpResponse(status=500)
        if country == COUNTRIES["US"]:
            profile.is_international = False
        else:
            profile.is_international = True

        profile.p_country = request.POST["country"]

        profile.signed_artist_agreement = True
        profile.save()
        return HttpResponse(status=200)
    return HttpResponseBadRequest()


def my_account_location_ajax(request):
    if request.method == "POST":
        rp = request.POST
        city = rp["value"]
        if city == "":
            return JsonResponse([], safe=False)
        g = geocoders.GoogleV3(api_key=settings.GOOGLE_MAPS_GEOCODING_API_KEY)
        # place,(lat,lng) = g.geocode(addr+" "+city +" "+zip)
        d = []
        try:
            places = list(g.geocode(city, exactly_one=False))  # type: ignore
            for place in places:
                d.append(place[0])
        except Exception as e:
            logger.error(e)

        if len(d) < 2:
            # LATER
            # locations = list(
            # Location.objects.filter(most_exact__contains=city)[:4])
            # for i in xrange(
            # len(locations)): d[i+len(d)] = locations[i].most_exact
            pass
        return JsonResponse([d], safe=False)
    return HttpResponseBadRequest()


@login_required
def my_account_location(request):
    t = loader.get_template("accounts/my-account/location.html")
    return utils.render_appropriately(request, t, {})


@csrf_exempt
def upload_photos_ajax(request):
    """
    upload_photos_ajax
    ajax call that takes in a bunch of files and turns them into photo objects,
    associating them with the profile making the request.
    """
    if request.method == "POST":
        return utils.JSON(process_uploaded_photo(request, request.FILES["photo"]))
    return HttpResponseBadRequest("No photo found")


def process_uploaded_photo(request, reqFile):
    "Handle individual photo file upload"
    profile = request.user.person.view
    photo = Photo.objects.create(profile=profile, caption="")
    try:
        photo.full_file = utils.image_operation(
            reqFile=reqFile, filename="full", isNew=True, ops=["thumb"], size=(900, 600)
        )
        photo.square_file = utils.image_operation(
            reqFile=reqFile,
            filename="square",
            isNew=True,
            ops=["crop_center"],
            size=(160, 160),
        )
        photo.thumbnail_file = utils.image_operation(
            reqFile=reqFile,
            filename="thumb",
            isNew=True,
            ops=["crop_center"],
            size=(40, 40),
        )
        photo.profile_file = utils.image_operation(
            reqFile=reqFile,
            filename="profile",
            isNew=True,
            ops=["thumb"],
            size=(400, 400),
        )

        photo.save()

        logger.info(photo)
        logger.info(photo.square_file)

        h = photo.full_file.height  # type: ignore
        w = photo.full_file.width  # type: ignore

        if w > h:
            photo.crop_left = (w - h) * 0.5
            photo.crop_right = w - ((w - h) * 0.5)
            photo.crop_top = 0
            photo.crop_bottom = h
        if h > w:
            photo.crop_left = 0
            photo.crop_right = w
            photo.crop_top = (h - w) * 0.3
            photo.crop_bottom = h - ((h - w) * 0.7)
        if h == w:
            photo.crop_left = 0
            photo.crop_right = w
            photo.crop_top = 0
            photo.crop_bottom = h

        photo.save()

        if profile.primary_photo is None:
            profile.primary_photo = photo
            profile.save()

        data = photo.jsonify(request)

        t = loader.get_template("common/photo_container.html")
        data["html"] = utils.render_appropriately(
            request, t, {"id": photo.id, "square_file": photo.square_file}
        ).content.decode("utf-8")

        return data

    except IOError:
        # cannot identify image file
        photo.delete()
        return {"error": "IOError"}


@login_required
def my_account_wallet(request):
    """
    shows hedera contract balance and activity
    """
    template = loader.get_template("accounts/my-account/wallet.html")

    hedera_enabled = settings.ENABLE_HTS

    profile = request.user.person.view
    wallet = None
    starter_tokens = None
    try:
        wallet = request.user.wallet
        starter_tokens = wallet.received_starter_tokens
    except User.wallet.RelatedObjectDoesNotExist:  # type: ignore
        pass

    unpaid_listens = Listen.objects.filter(
        Q(user=request.user) & Q(datetime_processed=None)
    ).aggregate(Sum("seconds"))["seconds__sum"]
    listens = Listen.objects.filter(
        Q(user=request.user) | Q(song__profile=profile)
    ).order_by("-datetime")[:100]

    return utils.render_appropriately(
        request,
        template,
        {
            "hedera_enabled": hedera_enabled,
            "starter_tokens": starter_tokens,
            "wallet": wallet,
            "unpaid_listens": unpaid_listens,
            "listens": listens,
            "contentclass": "dashboard wallet",
        },
    )


@login_required
def my_account_visuals(request):
    """
    my_account_photos
    ajax call that can both delete a photo and set a photo as a user's
    primary photo
    """
    t = loader.get_template("accounts/my-account/visuals.html")
    saved, error = False, False
    profile = request.user.person.view

    if request.GET.get("delete", False):
        if Photo.objects.filter(profile=profile, id=request.GET.get("delete")).exists():
            photo = Photo.objects.get(id=request.GET.get("delete"))
            if profile.primary_photo == photo:
                profile.primary_photo = None
                profile.save()
            photo.delete()
            saved = True
    elif request.GET.get("makePrimary", False):
        if Photo.objects.filter(
            profile=profile, id=request.GET.get("makePrimary")
        ).exists():
            profile.primary_photo = Photo.objects.get(id=request.GET.get("makePrimary"))
            profile.save()
            saved = True

    photos = Photo.objects.filter(profile=profile)
    videos = Video.objects.filter(profile=profile).all()
    primary_photo = profile.primary_photo
    return utils.render_appropriately(
        request,
        t,
        {
            "saved": saved,
            "error": error,
            "photos": photos,
            "videos": videos,
            "primary_photo": primary_photo,
            "contentclass": "dashboard visuals",
        },
    )


@login_required
def get_primary_photo(request):
    """
    get_primary_photo
    ajax call
    outputs the path of the user's thumbnail primary photo, as json
    generally used to dynamically update user tab in nav bar
    """
    profile = request.user.person.view
    data = {}
    if profile.primary_photo:
        data["path"] = profile.primary_photo.thumbnail_file.name
        data["id"] = profile.primary_photo.id
    return JsonResponse(data)


@login_required
def set_profile_pic(request):
    """
    set_profile_pic
    ajax call that takes in the id of a photo (photo_id) and returns the path
    of the user's primary photo thumbnail, as json
    """
    profile = request.user.person.view
    photo_id = request.POST["photo_id"]
    data = {}
    if Photo.objects.filter(profile=profile, id=photo_id).exists():
        photo = Photo.objects.get(id=photo_id)
        profile.primary_photo = photo
        profile.save()
        data["thumb_photo_path"] = photo.thumbnail_file.name
    return JsonResponse(data)


def validate_address(request):
    "Improper zip/state combination takes excessively long"
    try:
        p = request.POST
        g = geocoders.GoogleV3(api_key=settings.GOOGLE_MAPS_GEOCODING_API_KEY)
        g.geocode(
            "%s %s %s %s %s %s"
            % (
                p["address1"],
                p["address2"],
                p["city"],
                p.get("state", ""),
                p.get("zip", ""),
                p["country"],
            )
        )
        return True
    except:
        return True


@login_required
def my_account_legal(request):
    t = loader.get_template("accounts/my-account/legal.html")
    return utils.render_appropriately(request, t, {"contentclass": "dashboard legal"})


@csrf_exempt
def my_account_banner_ajax(request):
    banner = request.user.person.view.banner
    returnpath = False
    if "font" in request.POST:
        banner.font = request.POST["font"]
        banner.display_title = request.POST["display_title"] == "t"
        # Disable this for now
        # (request.POST['display_genre'] == 't')
        banner.display_genre = False
        banner.display_instrument = request.POST["display_instrument"] == "t"
        banner.display_location = request.POST["display_location"] == "t"
        banner.display_bar = request.POST["display_bar"] == "t"
        isUpload = request.POST["uploading_bool"] == "t"
        if not isUpload:
            banner.texture_chosen = "sky"
        if isUpload and banner.texture:
            banner.texture_chosen = "upload"
        banner.save()
    if "texture" in request.FILES:
        returnpath = True
        banner.texture_chosen = "upload"
        texture = request.FILES["texture"]
        banner.display_bar = True
        banner.texture = texture
        banner.save()

        banner.texture_resized = utils.image_operation(
            reqFile=banner.texture.path,
            filename="banner-resized",
            isNew=False,
            ops=["thumb"],
            size=(400, 400),
        )
        banner.save()

        if ImageFile(texture).width >= 960 and ImageFile(texture).height >= 200:
            banner.texture_cropped = utils.image_operation(
                reqFile=banner.texture.path,
                filename="banner-cropped",
                isNew=False,
                ops=["crop_center"],
                size=(965, 165),
            )
        else:
            banner.texture_cropped = banner.texture
    banner.save()
    if returnpath:
        return utils.JSON({"path": banner.cropped_path()})
    return HttpResponse(status=200)


@login_required
def upload_banner_temp(request):
    logger.info(request.POST)
    banner = request.user.person.view.banner
    texture = request.FILES["texture"]
    banner.texture_temp = texture
    banner.texture_temp_resized = utils.image_operation(
        reqFile=texture,
        filename="banner-resized",
        isNew=True,
        ops=["thumb"],
        size=(400, 400),
    )
    banner.save()
    return utils.JSON({"success": 1})


@login_required
def delete_temp_banner_texture(request):
    banner = request.user.person.view.banner
    if banner.texture_temp:
        banner.texture_temp.delete()
        banner.texture_temp_resized.delete()
        banner.save()
    return HttpResponse("delete")


@login_required
@csrf_exempt
def new_banner_submit(request):
    logger.info("new banner submit")
    banner = request.user.person.view.banner
    banner.texture = banner.texture_temp
    banner.texture_resized = banner.texture_temp_resized

    crop_top, crop_left, crop_right, crop_bottom = [
        int(float(request.POST[key])) for key in ["y", "x", "x2", "y2"]
    ]
    coords = (crop_left, crop_top, crop_right, crop_bottom)

    banner.texture_cropped = utils.image_operation(
        reqFile=banner.texture_temp,
        filename="banner_cropped",
        isNew=True,
        size=(965, 165),
        ops=["crop_coords", "thumb"],
        coords=coords,
    )

    banner.crop_top = crop_top
    banner.crop_bottom = crop_bottom
    banner.crop_left = crop_left
    banner.crop_right = crop_right
    banner.texture_chosen = "upload"
    banner.display_bar = True
    banner.save()

    return HttpResponse(banner.preview_tile())


def upload_video_ajax(request):
    "Adds a youtube video to your profile"
    view = request.user.person.view
    video_id = request.POST["video_id"]
    url = "https://www.googleapis.com/youtube/v3/videos?id={videoid}&key={apikey}&part=snippet".format(
        videoid=video_id, apikey=settings.YOUTUBE_DATA_API_KEY
    )
    video = requests.get(url)
    title = video.json()["items"][0]["snippet"]["title"]
    if title:
        video = Video(profile=view, title=title, embed_id=video_id)
        video.save()
        # returnDict = {'id': str(video.id), 'title': video.title}
        return render_to_response(
            "common/videolisting.html", {"video": video, "viewer": view}
        )
    return HttpResponseBadRequest("Sorry! we couldn't find your video!")


def delete_video_ajax(request):
    view = request.user.person.view
    video_id = request.GET["video_id"]
    vid = Video.objects.get(id=video_id, profile=view)
    vid.delete()
    return HttpResponse("deleted")


@login_required
def my_account_info(request):
    profile = request.user.person.view
    output = {"down_to_jam": profile.down_to_jam, "on_air": profile.on_air}
    return JsonResponse(output)


def privacy_policy(request):
    t = loader.get_template("privacy_policy.html")
    return utils.render_appropriately(request, t, {})


def terms_of_use(request):
    t = loader.get_template("terms_of_use.html")
    return utils.render_appropriately(request, t, {})


def copyright_agreement(request):
    t = loader.get_template("copyright.html")
    return utils.render_appropriately(request, t, {})


def artist_agreement(request):
    t = loader.get_template("artist_agreement.html")
    return utils.render_appropriately(request, t, {})


def accept_agreement(request):
    request.user.person.view.signed_artist_agreement = True
    request.user.person.view.save()
    return HttpResponse("signed it!")


def group_of_song_listings(request):
    get = request.GET
    return_data = {}
    try:
        songs_requested = get["data"].split(",")
        for song_id in songs_requested:
            return_data[song_id] = Song.objects.get(id=song_id).jsonify(request)

        return utils.JSON([return_data])
    except:
        return HttpResponse([{}])


@login_required
def delete_photo(request):
    view = request.user.person.view
    id_ = request.POST["id"]
    photo = Photo.objects.get(id=id_)

    # Verify that we own the photo, and delete it
    if photo.profile == view:
        # If this is currently the default photo,
        # set a different photo as the primary if one exists
        # or set primary to None. Just do we're not linking to
        # a photo that doesn't exist.
        if photo.is_primary():
            other_photos = Photo.objects.filter(profile=view).exclude(id=id_)
            if other_photos:
                view.primary_photo = other_photos[0]
            else:
                view.primary_photo = None
            view.save()
        photo.delete()
        return HttpResponse(status=200)
    return HttpResponse(status=403)


@login_required
def crop_photo(request):
    id_ = request.POST["id"]
    data = {}
    if Photo.objects.filter(profile=request.user.person.view, id=id_).exists():
        photo = Photo.objects.get(id=id_)
        crop_top = int(float(request.POST["y"]))
        if 0 > crop_top:
            crop_top = 0
        crop_left = int(float(request.POST["x"]))
        if 0 < crop_left:
            crop_left = 0
        crop_right = int(float(request.POST["x2"]))
        crop_bottom = int(float(request.POST["y2"]))
        coords = (crop_left, crop_top, crop_right, crop_bottom)

        photo.square_file = utils.image_operation(
            reqFile=photo.full_file.path,
            filename="square_usercropped",
            isNew=False,
            ops=["crop_coords", "thumb"],
            size=(160, 160),
            coords=coords,
        )
        photo.thumbnail_file = utils.image_operation(
            reqFile=photo.full_file.path,
            filename="thumb-usercropped",
            isNew=False,
            ops=["crop_coords", "thumb"],
            size=(40, 40),
            coords=coords,
        )
        photo.crop_top = crop_top
        photo.crop_bottom = crop_bottom
        photo.crop_left = crop_left
        photo.crop_right = crop_right
        photo.caption = request.POST["caption"]
        photo.save()
        data["square_photo_path"] = photo.square_file.name
        data["thumb_photo_path"] = photo.thumbnail_file.name
        # is below the best way to do this?
        data["isPrimaryPhoto"] = photo.is_primary()

    if id_ != "-1":
        return JsonResponse(data)
    return JsonResponse(data)


@login_required
def crop_banner(request):
    # Is it just me or is this retarded
    banner = request.user.person.view.banner
    crop_top = int(float(request.POST["y"]))
    crop_left = int(float(request.POST["x"]))
    crop_right = int(float(request.POST["x2"]))
    crop_bottom = int(float(request.POST["y2"]))
    coords = (crop_left, crop_top, crop_right, crop_bottom)

    banner.texture_cropped = utils.image_operation(
        reqFile=banner.texture.path,
        filename="square_usercropped",
        isNew=False,
        size=(965, 165),
        ops=["crop_coords", "thumb"],
        coords=coords,
    )
    banner.crop_top = crop_top
    banner.crop_bottom = crop_bottom
    banner.crop_left = crop_left
    banner.crop_right = crop_right
    banner.save()

    return HttpResponse(banner.preview_tile())


@login_required
def get_photo_details(request):
    """
    get_photo_details
    ajax call - GET request
    takes a photo id and returns a bunch of the corresponding photo's
    attributes, as json
    """
    data = {}
    _id = request.GET["id"]
    if Photo.objects.filter(profile=request.user.person.view, id=_id).exists():
        photo = Photo.objects.get(id=_id)
        data["photo_path"] = "/" + photo.profile_file.name
        data["x"] = photo.crop_left
        data["y"] = photo.crop_top
        data["x2"] = photo.crop_right
        data["y2"] = photo.crop_bottom
        data["width"] = photo.full_file.width
        data["height"] = photo.full_file.height
        data["width_prof"] = photo.profile_file.width
        data["height_prof"] = photo.profile_file.height
        data["caption"] = photo.caption
        data["isProfilePhoto"] = photo.is_primary()
    return JsonResponse(data)


@login_required
def get_banner_ajax(request):
    banner = request.user.person.view.banner
    data = {}
    if banner.texture:
        data = {
            "path": "/" + banner.texture_resized.name,
            "crop_left": banner.crop_left,
            "crop_right": banner.crop_right,
            "crop_top": banner.crop_top,
            "crop_bottom": banner.crop_bottom,
            "texture_width": banner.texture.width,
            "texture_height": banner.texture.height,
            "texture_resized_width": banner.texture_resized.width,
            "texture_resized_height": banner.texture_resized.height,
        }
    return JsonResponse(data)


@login_required
@csrf_exempt
def get_banner_upload_data(request):
    banner = request.user.person.view.banner
    data = {}
    if banner.texture_temp:
        data = {
            "path": "/" + banner.texture_temp_resized.name,
            "texture_width": banner.texture_temp.width,
            "texture_height": banner.texture_temp.height,
            "texture_resized_width": banner.texture_temp_resized.width,
            "texture_resized_height": banner.texture_temp_resized.height,
        }
    return JsonResponse(data)


@login_required
def my_account_payment(request):
    t = loader.get_template("accounts/my-account/payment.html")
    try:
        bank = BankInfo.objects.get(profile=request.user.person.view)
    except ObjectDoesNotExist:
        bank = None

    return utils.render_appropriately(
        request,
        t,
        {
            "contentclass": "dashboard payment",
            "bank": bank,
            "profile": request.user.person.view,
            "can_cash_out": request.user.person.view.get_total_profit_as_float() > 0.5,
            "has_made_profit": request.user.person.view.get_total_profit_as_float()
            > 0.0,
            "has_made_money_before": Receipt.objects.filter(
                profile=request.user.person.view
            ).exists(),
        },
    )


def send_feedback(request):
    username = request.user.person.view.name
    user_email = request.user.email
    subject = request.POST["subject"]
    message = request.POST["message"]
    result = utils.sendemail(
        "{}: {}".format(username, subject),
        "feedback@{}".format(settings.BASE_URL),
        "Reply-to email: {}\n\nMessage:\n{}".format(user_email, message),
    )
    if result:
        return HttpResponse("message sent")
    return HttpResponse("there was a problem sending")


@csrf_exempt
def send_invites(request):
    emails = request.POST["emails"]
    join_url = request.build_absolute_uri(reverse("join_index"))
    result = utils.sendemail_template(
        emails.split(","),
        "email_notifications/invitation.html",
        {"user": request.user, "join_url": join_url},
    )
    if result:
        return HttpResponse("invites sent")
    return HttpResponse("there was a problem sending")


def fandlib_ajax(request):
    "Give an id, get a song's jsonify data"
    t = loader.get_template("common/songlisting_div.html")
    song = Song.objects.get(id=request.GET["songid"])
    return utils.render_appropriately(
        request,
        t,
        {"song": song, "view": request.user.profile, "profile": song.profile},
    )


@login_required
def get_fan_feed(request):
    user = request.user
    page = int(request.GET.get("page", 1))
    feeds = Feed.decorated_fan_feed_for(user, request, page)
    t = loader.get_template("accounts/fan-feed.html")
    html = utils.render_appropriately(request, t, {"feeds": feeds})
    return HttpResponse(html)


@login_required
def export_user_emails(request):
    if request.user.is_staff:
        qs = User.objects.all().order_by("date_joined")

        header_row = [
            "first name",
            "last name",
            "email",
            "date joined",
            "last login",
            "verified",
        ]

        def get_data(user):
            try:
                verified = user.person.verified
            except:
                verified = False
            return [
                user.first_name,
                user.last_name,
                user.email,
                user.date_joined,
                user.last_login,
                verified,
            ]

        # StreamingHttpResponse requires a File-like class that has a 'write' method
        class Echo:
            def write(self, value):
                return value

        def iter_items(items, pseudo_buffer):
            writer = csv.writer(pseudo_buffer)
            yield writer.writerow(header_row)

            for item in items:
                yield writer.writerow(get_data(item))

        def get_response(queryset):
            response = StreamingHttpResponse(
                streaming_content=(iter_items(queryset, Echo())),
                content_type="text/csv",
            )
            response[
                "Content-Disposition"
            ] = "attachment;filename=user_export_{}.csv".format(datetime.date.today())
            return response

        return get_response(qs)
    return HttpResponseBadRequest()


@login_required
def send_jam(request):
    if request.user.is_active is False or request.user.profile.deactivated is True:
        logger.info("User account is inactive or has been deactivated")
    else:
        if request.method == "POST" and request.user.person.profile.allow_send_receive:
            to_account = request.POST["to_account"]
            amount = int(request.POST["amount"]) * settings.TOKEN_MULTIPLIER
            if amount < 0:
                return HttpResponseBadRequest("amount must be positive")
            memo = request.POST["memo"]
            password = request.POST["pass"]

            user = authenticate(email=request.user.email, password=password)
            if user is None:
                return HttpResponse("f")
            else:
                data = []
                data.append(
                    hedera_utils.create_token_transfer_json_data(
                        request.user.wallet.hedera_account_id,
                        settings.PRIVATE_KEY_PLACEHOLDER,
                        to_accounts=[(to_account, amount)],
                    )
                )

                # TODO: possibly add a facilitation fee
                # facilitation_fee=facilitation_fee,
                tokentransfer = HTSTokenTransfer(
                    listen=None,
                    from_user=request.user,
                    for_song=None,
                    value=amount,
                    memo=memo,
                    data=data,
                )
                tokentransfer.save()
                tokentransfer.transfer_token(
                    request.session[settings.PRIVATE_KEY_SESSION_KEY]
                )

            return HttpResponse("t")
    return HttpResponse("f")
