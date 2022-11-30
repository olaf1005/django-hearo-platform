import logging
import re
import json
import os
import datetime
from django.utils import timezone

from the_hearo_team import send_msg

from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

import utils
import hedera_utils

from tartar import CallMeMaybe, GangnamStyle

import infrared

from media.models import Song, Album, Listen
from accounts.models import DownloadCharge, HTSTokenTransfer, Membership, Profile

from utils import ajax_login_required


logger = logging.getLogger(__name__)


def song_cover(request, songid):
    try:
        song = Song.objects.get(pk=songid)
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("Song does not exist")

    img = song.get_cover()
    if img:
        with img as f:
            return HttpResponse(f.read(), content_type="image/jpeg")

    return HttpResponseBadRequest("No image")


def get_value_and_facilitation_fee(seconds_to_pay):
    # get value
    value = (float(seconds_to_pay) / 60) * settings.JAM_PER_MINUTE
    value = value * settings.TOKEN_MULTIPLIER

    # remove facilitation fee
    facilitation_fee = value * settings.FACILITATION_PERCENTAGE
    value = value - facilitation_fee
    return (value, facilitation_fee)


def _record_token_transfers(request, listen, first_stream_free, num_streams):
    if listen and (not listen.free or (first_stream_free and num_streams > 1)):
        # pay artists
        song = listen.song
        seconds_to_pay = listen.seconds - settings.FREE_LISTEN_SECONDS
        data = create_token_transfers_for_listen(request.user, song, seconds_to_pay)
        # TODO: if the above fails still need to record the listen but need to send an email
        # to users without a wallet associated with the profile
        # before we do this however we need a test to verify functionality in
        # case of regression
        if data:
            value, facilitation_fee = get_value_and_facilitation_fee(seconds_to_pay)
            tokentransfer = HTSTokenTransfer(
                listen=listen,
                from_user=request.user,
                for_song=song,
                value=value,
                facilitation_fee=facilitation_fee,
                data=data,
            )
            tokentransfer.save()
            tokentransfer.transfer_token(
                request.session[settings.PRIVATE_KEY_SESSION_KEY]
            )
            listen.datetime_processed = timezone.now()
            listen.save()


def create_token_transfers_for_listen(user, song, seconds_to_pay):
    tokentransfers = []

    try:
        value, facilitation_fee = get_value_and_facilitation_fee(seconds_to_pay)

        try:
            org_membership = song.profile.organization.membership_set.all()
        except:
            org_membership = Membership.objects.none()

        org_membership_cnt = org_membership.count()

        # if we have one membership
        if org_membership_cnt == 0:
            # TODO: this should be fixed using the organization
            # e.g.
            # >>> org=Profile.objects.get(pk=14657).organization

            # If for some reason all membership have been removed from the
            # organization then we can still attribute the song to the profile
            to_user = song.profile.user
            # TODO: investigate the cause of this error
            assert (
                to_user is not None
            ), "Profile not attached to any user and has no membership"

            # If the user has been deactivated, transfer the funds to our treasury
            # and mark the other account as suspicious keep them rolling rolling!
            # any suspicious account then also transfers back to treasury
            if (
                to_user.is_active is False
                or to_user.profile.deactivated is True
                or to_user.profile.suspicious is True
            ):
                # Since we are marking the user as suspicious we stil want to transfer
                # jam back to treasury and allow the user to continue to use the site
                # hence, HTSTokenTransfer.transfer_token doesn't need to consider
                # the suspcious flag
                user.profile.suspicious = True
                user.profile.save()
                to_user.profile.suspicious = True
                to_user.profile.save()

                tokentransfer = hedera_utils.create_token_transfer_json_data(
                    user.wallet.hedera_account_id,
                    settings.PRIVATE_KEY_PLACEHOLDER,
                    # TODO: make sure that None is the right parameter here when making a
                    # treasury payment
                    to_accounts=[(None, value)],
                )
            else:
                tokentransfer = hedera_utils.create_token_transfer_json_data(
                    user.wallet.hedera_account_id,
                    settings.PRIVATE_KEY_PLACEHOLDER,
                    to_accounts=[(to_user.wallet.hedera_account_id, value)],
                )

            tokentransfers.append(tokentransfer)
        elif org_membership_cnt == 1:
            # If there is only one member, ensure they receive 100%
            member = org_membership[0]
            to_user = member.person.user
            assert to_user is not None, "Person has no user attached"

            # If the user has been deactivated, transfer the funds to our treasury
            # and mark the other account as suspicious keep them rolling rolling!
            # any suspicious account then also transfers back to treasury
            if (
                to_user.is_active is False
                or to_user.profile.deactivated is True
                or to_user.profile.suspicious is True
            ):
                tokentransfer = hedera_utils.create_token_transfer_json_data(
                    user.wallet.hedera_account_id,
                    settings.PRIVATE_KEY_PLACEHOLDER,
                    # TODO: make sure that None is the right parameter here when making a
                    # treasury payment
                    to_accounts=[(None, value)],
                )
                # Since we are marking the user as suspicious we stil want to transfer
                # jam back to treasury and allow the user to continue to use the site
                # hence, HTSTokenTransfer.transfer_token doesn't need to consider
                # the suspcious flag
                user.profile.suspicious = True
                user.profile.save()
                to_user.profile.suspicious = True
                to_user.profile.save()
            else:
                tokentransfer = hedera_utils.create_token_transfer_json_data(
                    user.wallet.hedera_account_id,
                    settings.PRIVATE_KEY_PLACEHOLDER,
                    to_accounts=[(to_user.wallet.hedera_account_id, value)],
                )

            tokentransfers.append(tokentransfer)
        else:
            # get the total, should sum up to 1.0
            sum_revenue_split = sum([m.revenue_split for m in org_membership])
            if sum_revenue_split == 0:
                logger.info(" - fixing split which was set to 0")
                correct_split = 1.0 / len(org_membership)
                for member in org_membership:
                    member.revenue_split = correct_split
                    member.save()
            if sum_revenue_split == 1.0:
                logger.info(" - revenue split is for 1")
            else:
                logger.info(" - fixing split which was not equal to 1")
                # take revenue split and calculate each persons as a percentage of the total
                # total should always be 1 so
                for member in org_membership:
                    correct_split = member.revenue_split / 1.0
                    if member.revenue_split != correct_split:
                        member.revenue_split = correct_split
                        member.save()

            to_accounts = []
            for member in org_membership:
                partial_value = member.revenue_split * value
                logger.info(
                    " - %s paying %s - %s split", user, member, member.revenue_split
                )
                to_user = member.person.user

                # If the user has been deactivated, transfer the funds to our treasury
                # and mark the other account as suspicious keep them rolling rolling!
                # any suspicious account then also transfers back to treasury
                if (
                    to_user.is_active is False
                    or to_user.profile.deactivated is True
                    or to_user.profile.suspicious is True
                ):

                    # Since we are marking the user as suspicious we stil want to transfer
                    # jam back to treasury and allow the user to continue to use the site
                    # hence, HTSTokenTransfer.transfer_token doesn't need to consider
                    # the suspcious flag
                    user.profile.suspicious = True
                    user.profile.save()
                    to_user.profile.suspicious = True
                    to_user.profile.save()

                    to_accounts += (None, partial_value)
                else:
                    to_accounts += (to_user.wallet.hedera_account_id, partial_value)

            tokentransfer = hedera_utils.create_token_transfer_json_data(
                user.wallet.hedera_account_id,
                settings.PRIVATE_KEY_PLACEHOLDER,
                to_accounts=to_accounts,
            )
            tokentransfers.append(tokentransfer)

        # treasury payment
        tokentransfer = hedera_utils.create_token_transfer_json_data(
            user.wallet.hedera_account_id,
            settings.PRIVATE_KEY_PLACEHOLDER,
            # TODO: make sure that None is the right parameter here when making a
            # treasury payment
            to_accounts=[(None, facilitation_fee)],
        )
        tokentransfers.append(tokentransfer)

        logger.debug(" - recorded transactions successfully")
        return tokentransfers
    except AssertionError as e:
        logger.error(e)
    except Exception as e:
        logger.exception(
            "error calculating token transactions for listen by for %s - listening for to %s",
            user,
            song,
        )


@ajax_login_required
def song_listen(request):
    # init some vars
    num_streams = 0
    first_stream_free = False
    is_free = False
    # record the song listen
    listen = None
    song_id = int(request.POST["song_id"])
    seconds = int(request.POST["seconds"])
    logger.debug("Listened to song %s for %s seconds", song_id, seconds)
    if seconds > 0:
        try:
            song = Song.objects.get(pk=song_id)
            is_free = bool(song.download_type == "free")
            first_stream_free = bool(song.download_type == "none")
            if first_stream_free:
                num_streams = Listen.objects.filter(
                    user=request.user, song=song
                ).count()
            if song.profile.user != request.user:
                listen = Listen(
                    user=request.user, song=song, seconds=seconds, free=is_free
                )
                listen.save()
        except Profile.DoesNotExist:
            pass

    try:
        _record_token_transfers(request, listen, first_stream_free, num_streams)
    except:
        # We pass here because listens without token transfers will be looked
        # at and we will create the token transfers at the right time when
        # the user logs in
        # TODO: send users without an associated wallet an email
        pass

    return HttpResponse(200)


@login_required  # type: ignore
def get_download_status(request):
    view = request.user.person.view

    download_id = request.GET["download_id"]
    try:
        dl = DownloadCharge.objects.get(profile=view, id=download_id)
    except ObjectDoesNotExist:
        # TODO: this is untested
        data = {"status": "error"}
        return HttpResponse(json.dumps(data))

    packageid = dl.packageid
    GN = GangnamStyle(infrared.Context(settings.CONFIG))
    url = GN.geturl(packageid)

    # TODO: this is untested
    data = {"status": "ready", "url": url} if url else {"status": "waiting"}

    return HttpResponse(json.dumps(data))


@login_required
def real_delete(request):
    """should ONLY be called from s3 upload failing"""
    profile = request.user.person.view
    _id = request.POST["id"]
    song = Song.objects.get(profile=profile, id=_id)
    song.delete()
    # TODO: unregister from callmemaybe?
    return HttpResponse(200)


@login_required
def get_signature(request):
    profile = request.user.person.view
    name = request.GET["s3_object_name"]
    mime = request.GET["s3_object_type"]

    albumid = request.GET.get("albumid") or None

    # Strip the filename off the end
    songtitle, ext = os.path.splitext(name)
    # Max length
    songtitle = songtitle[:100]
    sig = CallMeMaybe.generate_signature(name, mime)

    # create song object in processing state
    newsong = Song.objects.create(
        processing=True,
        online=False,
        visible=True,
        price=0.69,
        download_type="normal",
        title=songtitle,
        profile=profile,
        keyword=sig["name"],  # NEED THIS TO REGISTER TARTAR (dont jsonify)
    )

    if albumid:
        album = Album.objects.get(pk=int(albumid))
        if album.profile != profile:
            raise PermissionDenied("Please login as the user")

        append_song(newsong, album)

    ret = {
        "url": sig["url"],
        "signed_request": sig["signed_request"],
        "data": newsong.jsonify(request),
    }

    logger.info("song_upload_init %s", name)
    return HttpResponse(json.dumps(ret))


@login_required
def cmm_register(request):
    """called after the upload to s3 is completed successfully"""
    profile = request.user.person.view
    _id = request.POST["id"]
    song = Song.objects.get(profile=profile, id=_id)

    ctx = infrared.Context(settings.CONFIG)
    cmm = CallMeMaybe(ctx)
    try:
        cmm.register(song.id, song.keyword, profile.id, CallMeMaybe.Song)
    except Exception as e:
        song.state_info = repr(e)
        song.save()

        logger.exception(
            "Song %s with id %d (%s) failed to upload: %s",
            song.title,
            song.id,
            profile.name,
            e,
        )
        send_msg(
            profile,
            "Tune.fm! Failed upload",
            "We're sorry for the "
            "inconvenience! The song {!r} failed to upload "
            "successfully. We will have a look and attempt "
            "to resolve the issue.".format(song.title),
        )

        try:
            admin = Profile.objects.get(email="dnordberg@gmail.com")
            send_msg(
                admin,
                "FAILED UPLOAD",
                "Tune.fm! Failed to upload. Id {!r}".format(song.id),
            )
        except:
            pass
        return HttpResponse("Insert Error", status=500)

    logger.info("song_upload: %s", song.title)

    return HttpResponse(200)


def album_info(request):
    """this is maybe too similar to get_album, but serves enough of a
    difference (1 doesn't care about security) that i think it's worth it
    """
    rg = request.GET
    albumid = rg["id"]
    album = Album.objects.get(id=albumid)
    return HttpResponse(json.dumps(album.jsonify(request)))


def append_song(song, album=None):
    """
    Songs ajax views for Music in Dashboard

    I/P: Song
         Album (optional)

    Prepend song to beginning of album, as track #1
    Shifts the rest of the songs down by 1 track num
    If no album is provided, the profile's non-album songs
    are treated as the album.
    """

    # Make sure songs are never appended to other users' albums
    if album:
        if album.profile != song.profile:
            raise PermissionDenied("Please login as the user")
        else:
            try:
                last_track = album.songs.all().order_by("-track_num")[0].track_num
            except IndexError:
                last_track = 0
    else:
        last_track = (
            song.profile.get_non_album_songs().order_by("-track_num")[0].track_num
        )

    song.album = album
    song.track_num = last_track + 1
    song.save()
    return song


def _reorder_songs(song, n):
    """
    reorder_songs
    Song, Int -> Song

    Given a Song song and Int n, we move that song to the n
    track_num spot amongst its siblings (other songs on the album, or
    in the case of a non-album song, all other non-album songs).
    Then, depending on which side of n the song came from, we
    reorder the other songs accordingly.

    Examples:

    Given an album of songs {a:1, b:2, c:3, X:4, e:5, f:6}, moving song d (spot
    4) to spot 2 results in the album {a:1, X:2, b:3, c:4, e:5, f:6}

    Given an album of songs {a:1, X:2, c:3, d:4, e:5, f:6}, moving song b (spot
    2) to spot 4 results in the album {a:1, c:2, d:3, X:4, e:5, f:6}

    Get song's siblings from its album or, if it's not in an album,
    get the user's other non-album songs.
    """

    currentalbum = song.album

    if currentalbum:
        songs = song.album.songs.all()
    else:
        songs = song.profile.get_non_album_songs()

    # Put them in order
    songs = songs.order_by("track_num")

    songs_before = list(songs.filter(track_num__lt=n).exclude(pk=song.pk))
    songs_after = list(songs.filter(track_num__gte=n).exclude(pk=song.pk))
    songs = songs_before + [song] + songs_after

    for i, s in enumerate(songs, 1):
        if s.track_num != i:
            Song.objects.filter(pk=s.id).update(track_num=i)

    all_music = song.profile.get_songs_by_album()
    return_data = {}

    for a_ in all_music:
        return_data[a_] = number_songs(all_music[a_], False)

    return utils.JSON(return_data)


@login_required
def reorder_songs_ajax(request):
    """
    AJAX wrapper for reorder_songs, and moving them between albums (or
    non-album)

    I/P:
    songid:  int, id of song
    albumid: int, id of album
    n:       spot the song should be in
    O/P: [{ id: track_num}] list of song's siblings
    """

    song = Song.objects.get(id=int(request.POST["songid"]))
    albumid = int(request.POST["albumid"])
    view = request.user.person.view
    n = int(request.POST["n"])

    if song.profile != view:
        raise PermissionDenied("Please login as the user")

    # The album that has the song at the time the reordering is requested
    oldalbum = song.album

    # Zero is non-album, so if we're dropping it into an album...
    if albumid != 0:
        # If they're trying to put the song into an album
        desiredalbum = Album.objects.get(id=int(albumid))

        if desiredalbum.profile != request.user.person.view:
            raise PermissionDenied("Please login as the user")

        # If the album stays the same can pass and just reorder, so check
        # only if the desiredalbum differs
        if oldalbum != desiredalbum:
            # Remove album from the song so we can renumber songs from the oldalbum
            song.album = None
            song.save()

            if oldalbum:
                # Once that song is gone, renumber the old album's track_nums to
                # maintain order.
                number_songs(oldalbum.songs.all())
            else:
                number_songs(view.get_non_album_songs())

            # Finally, add it to the desired album
            song.album = desiredalbum
            song.save()
    else:
        # If we're moving it to album 0, non-album, pull it out of the old
        # album.
        if oldalbum:
            # Remove the song to old album relationship
            song.album = None
            song.track_num = None
            song.save()
            number_songs(oldalbum.songs.all())

    # Now that we've sorted out the album, reorder it
    return _reorder_songs(song, n)


def number_songs(songs, renumber=True):
    """
    number_songs

    Given a QuerySet of songs, renumber them incrementally starting with 1.

    Basically, preserve the order of the songs but fix possible gaps in the
    track_nums Used to fix the track_num gap a song leaves when it gets moved
    from one album to another.
    """

    songs = songs.order_by("track_num")

    return_data = {}

    for i, s in enumerate(songs, 1):
        if s.track_num != i:
            Song.objects.filter(pk=s.id).update(track_num=i)
        return_data[s.id] = s.track_num

    return return_data


@login_required
def edit_music_entity_details(request, entity_type):
    """
    AJAX endpoint for editing song or album's information: title, price, or
    download_type

    I/P: id - entity id (int)
            AND
        title - entity title (str)
            AND/OR
        price - entity price (0 <= float <= 9.99)
            AND/OR
        download - entity download type (str of 'normal', 'name_price', 'none',
        'free')
            AND/OR
        year_released - only for albums (int between 1970 and current year)

    entity_type is given by media.urls
    """

    if request.method != "POST":
        # Must be a POST
        return HttpResponseBadRequest("POST required")

    p = request.POST

    # Extract data
    download_type = p.get("download_type", None)
    entity_id = int(request.POST["id"])
    price = p.get("price", None)
    title = p.get("title", None)
    year_released = p.get("year_released", None)

    if price:
        price = float(price)

    logger.info("price: %s %s", price, type(price))

    attrs_being_changed = {}

    view = request.user.person.view

    entity = (
        Song.objects.get(id=entity_id)
        if entity_type == "song"
        else Album.objects.get(id=entity_id)
    )

    # Check for authorization on entity
    if entity.profile != view:
        raise PermissionDenied("Please login as the user")

    # Try parsing price
    if price is not None:
        try:
            price = float(price)
            entity.price = max(min(price, 9.99), 0)
        except ValueError:
            return HttpResponse(500)

    if download_type and download_type in ["normal", "name_price", "none"]:
        entity.download_type = download_type
        attrs_being_changed["download_type"] = download_type

    if entity.download_type in ["normal", "name_price", "free"]:
        if entity.price == 0 and entity.download_type == "normal":
            entity.download_type = "free"

        elif entity.price != 0 and entity.download_type == "free":
            entity.download_type = "normal"

        attrs_being_changed["price"] = price

    if title and len(title) > 0:
        entity.title = title
        attrs_being_changed["title"] = title

    if year_released and entity_type == "album":
        entity.year_released = year_released
        attrs_being_changed["year_released"] = year_released

    entity.save()

    logger.info(
        "edit_%s - %s - %s",
        entity_type,
        entity.title,
        str(attrs_being_changed).replace("'", '"'),
    )

    return HttpResponse(200)


@login_required
def delete_song_ajax(request):
    """
    Set a profile's own song to deleted = True.
    I/P: songid: int
    """

    p = request.POST
    view = request.user.person.view

    # Check auth on song
    song = Song.objects.get(id=p["songid"])
    if song.profile != view:
        raise PermissionDenied("Please login as the user")

    # If their papers are in order, delete the song.
    song.deleted = True
    song.save()
    logger.info("%s %s", song, p["songid"])
    return HttpResponse(200)


def log_compressed_clientside_error(request):
    p = request.POST
    logger.error("songtype_error: %s %s", p["filename"], p["reason"])
    return HttpResponse(200)


# Albums ajax views for Music in Dashboard


def create_album(request):
    """
    User creates a new album.

    O/P : album admin view template rendered : str
    """

    view = request.user.person.view
    user_albums = Album.objects.filter(profile=view, deleted=False)

    # Default new album name
    title = "New Album"

    # Incremement digit after New Album to New Album 1, New Album 2, etc if
    # user has created and not renamed prior albums.
    if user_albums.exists():
        i = 0
        for user_album in user_albums:
            match = re.match(r"New Album\s?(?P<digit>\d+)?", user_album.title)
            if match:
                digit = match.group("digit")
                if digit:
                    if int(digit) > i:
                        i = int(match.group("digit")) + 1  # For each
                else:
                    # If we've found at least a single "New Album",
                    # we have to have at least "New Album 1" next.
                    i = max(i, 1)  # type: ignore

        if i > 0:
            title += " %d" % i

    # Default values for an album:
    album = Album(
        profile=view,
        title=title,
        year_released=datetime.datetime.now().year,
        price=4.99,
        download_type="normal",
    )
    album.save()

    # Return data: generate the album admin view and return it.
    # It will be injected into the DOM with jQuery.
    has_singles = view.get_non_album_songs().exists()
    html = loader.render_to_string(
        "common/album_admin_view.html", {"album": album, "has_singles": has_singles}
    )

    logger.info("create_album")

    return utils.JSON({"html": html})


def delete_album_ajax(request):
    """
    User deletes an album.

    I/P: albumid : int
    """

    p = request.POST
    view = request.user.person.view

    album = Album.objects.get(id=p["albumid"])

    if album.profile != view:
        raise PermissionDenied("Please login as the user")

    album.deleted = True
    album.save()

    for song in album.songs.all():
        song.deleted = True
        song.save()

    return HttpResponse(200)


def album_cover_ajax(request):
    """
    Upload an image file and set it as an album cover.
    I/P: albumid: int
    """

    p = request.POST
    view = request.user.person.view

    # Check auth
    album = Album.objects.get(id=p["albumid"])
    if album.profile != view:
        raise PermissionDenied("Please login as the user")

    cover_file = request.FILES["cover_file"]

    # Do the image cropping
    album.full_cover = utils.image_operation(
        reqFile=cover_file,
        filename="full",
        isNew=True,
        ops=["crop_center"],
        size=(550, 500),
    )
    album.medium_cover = utils.image_operation(
        reqFile=cover_file,
        filename="medium",
        isNew=True,
        ops=["crop_center"],
        size=(400, 400),
    )
    album.small_cover = utils.image_operation(
        reqFile=cover_file,
        filename="small",
        isNew=True,
        ops=["crop_center"],
        size=(200, 200),
    )

    album.save()
    return utils.JSON({"path": "/%s" % album.small_cover.url})  # type: ignore


def get_album(request):
    rg = request.GET
    albumid = rg["albumid"]
    album = Album.objects.get(id=albumid, profile=request.user.person.view)
    return utils.JSON([album.jsonify(request)])


def get_album_songs(request):
    rg = request.GET
    albumid = rg["albumid"]
    album = Album.objects.get(id=albumid)
    return utils.JSON([song.jsonify(request) for song in album.get_online_songs()])


def save_album_songs(request):
    view = request.user.person.view
    if request.method == "POST":
        rp = request.POST
        songs = rp["songs"].split(",")
        albumid = rp["albumid"]
        album = Album.objects.get(profile=view, id=int(albumid))
        # check to see if all the songids are valid
        for songid in songs:
            if not Song.objects.filter(profile=view, id=songid).exists():
                return HttpResponseBadRequest(
                    "Sorry, we can't find those songs in your name"
                )

        # remove all the old songs from the album
        album.songs.clear()

        # add those new songs
        for i, songid in enumerate(songs, 1):
            Song.objects.filter(profile=view, pk=songid).update(
                track_num=i, album=album
            )

        return HttpResponse("saved")
    return HttpResponseBadRequest()


def song_view(request, slug):
    embed = bool(request.GET.get("embed", 0))
    t = loader.get_template("media/song.html")
    song_get = Song.objects.get(keyword=slug)
    if song_get.profile.profile_private:
        raise Http404()
    plays = song_get.plays.all().order_by("timestamp")
    reviews = song_get.reviews.all()
    as_listing = song_get.as_music_listing(request)
    if embed:
        base_embed = "base_embed.html"
    else:
        base_embed = "base.html"
    response = {
        "base_embed": base_embed,
        "embed": embed,
        "song": song_get,
        "plays": plays,
        "reviews": reviews,
        "as_listing": as_listing,
    }
    return utils.render_appropriately(request, t, response)


def album_view(request, slug):
    t = loader.get_template("media/album.html")
    album_get = Album.objects.get(keyword=slug)
    if album_get.profile.profile_private:
        raise Http404()
    reviews = album_get.reviews.all()
    plays = sum([song.plays.count() for song in album_get.songs.all()])
    return utils.render_appropriately(
        request, t, {"album": album_get, "reviews": reviews, "plays": plays}
    )
