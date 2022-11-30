import logging
from functools import reduce

import django

django.setup()

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.template import loader

from tartar import GangnamStyle
import infrared
from accounts.models import MediaDownload, DownloadCharge
from media import TARTAR_FORMATS
from utils import render_appropriately
import the_hearo_team


logger = logging.getLogger("puller")


@login_required
def download_page(request, packageid):
    view = request.user.person.view
    t = loader.get_template("download.html")
    dl_id = packageid
    dl = DownloadCharge.objects.get(packageid=dl_id)
    if dl.profile != view:
        return HttpResponse(status=403)

    GN = GangnamStyle(infrared.Context(settings.CONFIG))
    if dl.packageid:
        url = GN.geturl(dl.packageid)
        return render_appropriately(
            request, t, {"url": url if url else "", "dlid": dl_id}
        )
    return HttpResponse("download not ready", status=500)


def song_package(format, song, album=None, i=None):
    """
    songs many to many with albums makes this tough, just include
    album when you're buying it *as* a download
    """
    meta = {}
    if album and album.year_released:
        meta["year"] = str(album.year_released)

    # TODO: more metadata
    tartar_format = TARTAR_FORMATS[format]
    return {
        "songid": song.id,
        "track_name": song.title,
        "artist_name": song.profile.name,
        "album_name": album.title if album else "",
        "track_number": i if i else 1,
        "track_total": 1 if not album else album.songs.count(),
        "targetformat": tartar_format,
        "meta_data": meta,
    }


def album_package(format, artist, album):
    songs = [
        song_package(format, song, album, i)
        for i, song in enumerate(album.get_online_songs(), 1)
    ]
    return {"name": artist.name + " - " + album.title, "songs": songs}


def artist_package(format, artist, songs, albums):
    folders = [album_package(format, artist, a) for a in albums]
    if songs:
        folders.append(
            {
                "name": artist.name + " - Singles",
                "songs": [song_package(format, s) for s in songs],
            }
        )
    return folders


def get_package(profile, songs, albums=[]):
    """
    profile is the requesting profile
    songs is a list of Song objects
    albums is a list of Album objects

    TODO: review this, why exactly are we using download_number??
    """

    download_number = MediaDownload.objects.filter(media__profile=profile).count()

    artists = {obj.profile: [[], []] for obj in albums + songs}
    for song in songs:
        artists[song.profile][0].append(song)
    for album in albums:
        artists[album.profile][1].append(album)

    format = profile.default_download_format

    artist_packages = [
        artist_package(format, a, lst[0], lst[1]) for a, lst in list(artists.items())
    ]

    # flatten the list of lists
    folders = [folder for a_package in artist_packages for folder in a_package]

    package = {
        "foldername": "Hearo_Download_" + str(download_number + 1),
        "method": "zip",  # will always be zip, but lets keep it in anyway
        "version": 1,
        "folders": folders,
    }
    return package


def request_download(profile, songs, albums=None):
    """give a profile, list of songs, and list of albums (MUST BE LIST)"""

    if albums is None:
        albums = []

    package = get_package(profile, songs, albums)

    GN = GangnamStyle(infrared.Context(settings.CONFIG))

    packageid = GN.requestdownload(profile.id, package)

    return (packageid, GN)


def update_pending_dl(status, update):
    """update will be of form {id : <packageid> , url : <dlurl> }"""
    if status == "online":
        packageid = update["id"]
        try:
            dl = DownloadCharge.objects.get(packageid=packageid)
        except ObjectDoesNotExist:
            msg = "Download Charge matching packageid {} does not exist".format(
                packageid
            )
            logger.error(msg, extra={"status": status, "update": update})
            return

        profile = dl.profile

        subject = "Download ready!"
        message = "You can grab it here! /download/?id=%s" % dl.id
        the_hearo_team.send_msg(profile, subject, message)

    elif status == "error":
        logger.error("Tartar reported 'error'", extra={"update": update})


def pull():
    GN = GangnamStyle(infrared.Context(settings.CONFIG))
    updates = GN.getupdates()

    if reduce(lambda a, b: a + len(b[1]), list(updates.items()), 0) == 0:
        logger.debug("no changes")
        return

    logger.info("DOWNLOAD changes at time %s: %s", str(timezone.now()), str(updates))
    logger.info(updates)
    for updatetype in updates:
        for update in updates[updatetype]:
            try:
                update_pending_dl(updatetype, update)
            except Exception as e:
                logger.exception(e)


if __name__ == "__main__":
    pull()
