# -*- coding: utf-8 -*-
"""
Should be called like this:

./manage.py bulk_import --catalog catalog.csv --directory ./rnb/rnb/ --userid 4143 --genre Rnb
"""
import logging
import os
import json
import glob
import csv
from optparse import make_option
from operator import itemgetter
from itertools import groupby
import requests

import boto
from boto.s3.key import Key

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.uploadedfile import File
from django.conf import settings

from accounts.models import Profile
from accounts import views as accviews
from media.models import Album, Song
from media import views as mediaviews

from django.test.client import RequestFactory


logger = logging.getLogger(__name__)

DEBUG = False

IMAGE_FORMATS = ["gif", "jpg", "jpeg", "png"]
AUDIO_FORMATS = ["wav", "flac", "aiff"]


"""May want to just replace these with a log message so we can continue and
reattempt failed saves"""


class SaveArtistPageError(Exception):
    pass


class SaveArtistVisualError(Exception):
    pass


class S3UploadSongError(Exception):
    pass


def register_and_upload_song(user, fpath, albumid=None):
    # if the audio format is valid
    if DEBUG:
        return True
    fname, ext = os.path.splitext(fpath)
    ext = ext[1:]
    basename = os.path.basename(fname)

    # remove any numbers from titles of songs in the already sorted list
    songtitle = basename.lstrip("0123456789.- ")

    if Song.objects.filter(
        title=songtitle, album_id=albumid, profile=user.person.view
    ).count():
        logger.warn("Song was already uploaded for profile %s", user.person.view)
        return True

    if ext in AUDIO_FORMATS:
        content_type = "audio/{}".format(ext)

        s3_object_name = "{}.{}".format(songtitle, ext)

        # post to get-signature to get the id of the file to upload
        factory = RequestFactory()
        data = dict(s3_object_name=s3_object_name, s3_object_type=content_type,)
        if albumid:
            data["albumid"] = albumid
        request = factory.get("/get-signature/", data)
        request.user = user

        response = mediaviews.get_signature(request)
        response = json.loads(response.content)

        # upload the file
        key = response["url"].lstrip(
            "https://{}.s3.amazonaws.com/".format(settings.S3_BUCKET)
        )

        if not upload_to_s3(fpath, key, content_type):
            raise S3UploadSongError("Failed to upload {!r}".format(fpath))

        # then register the song as needing to be processed
        factory = RequestFactory()
        data = dict(id=response["data"]["id"])
        request = factory.post("/cmm-register/", data)
        request.user = user

        response_2 = mediaviews.cmm_register(request)
        if response_2.status_code == 200:
            logger.info("Successfully uploaded and registered song %s", fpath)
        else:
            logger.error("Failed to uploaded and registered song %s", fpath)
        return True
    else:
        logger.error(
            "Audio has an invalid format: %s - %s - %s",
            user.person.view.name,
            ext,
            fpath,
        )
        return False


def upload_to_s3(fname, key, content_type):
    """Uploads a file to our hearo uploaded songs bucket and returns the
    filesize of the uploaded song
    """
    s3 = boto.connect_s3(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)
    bucket = s3.lookup(settings.S3_BUCKET)
    s3key = bucket.new_key(key)
    s3key.set_metadata("Content-Type", content_type)
    res = s3key.set_contents_from_file(open(fname, "r"))
    logger.info("Uploaded %s for song %s", res, fname)
    return res


class CatalogManager:
    def __init__(self, catalog):
        with open(catalog, "rb") as csvfile:
            self.catalogdata = list(csv.DictReader(csvfile))
            sortkeyfn = itemgetter("Artist")
            self.catalog_by_artist = {
                key: list(valuesiter)
                for key, valuesiter in groupby(self.catalogdata, key=sortkeyfn)
            }


class BulkImporter:
    def __init__(
        self,
        user_id,
        directory,
        catalog,
        genre,
        address1=None,
        address2=None,
        state=None,
        zipcode=None,
        city=None,
        country=None,
    ):
        self.user = User.objects.get(pk=user_id)
        self.directory = directory
        self.catalog = CatalogManager(catalog)
        self.genre = genre
        self.address1 = address1
        self.address2 = address2
        self.state = state
        self.zipcode = zipcode
        self.city = city
        self.country = country

    def set_view(self, profile):
        "This sets up the current view to the page being processed"
        person = self.user.person
        person.view = profile
        person.save()

    def add_page(self, pagepath):
        "Check if the profile exists, if it doesn't, create it"
        logger.debug("ADD PAGE: %s", pagepath)

        artist_name = pagepath.strip()

        exists = False

        try:
            profile = Profile.objects.get(name=artist_name)
            logger.warn(
                "Profile already exists, skipping creation for profile %s", profile
            )
            exists = True
        except Profile.DoesNotExist:
            factory = RequestFactory()

            data = dict(
                account_type="band",
                name=artist_name,
                is_musician="0",
                instruments=None,
                join_band="f",
                write_music="f",
                teacher="f",
                dj="f",
                producer="f",
                engineer="f",
                city=None,
                genre=self.genre,
            )
            request = factory.post("/my-account/create-page-ajax/", data)
            request.user = self.user

            response = accviews.create_page_ajax(request)

            if response.status_code == 200:
                logger.info("Saved artist page: %s", artist_name)
            else:
                raise SaveArtistPageError(
                    "Failed to save artist page: {!r}".format(artist_name)
                )

            js = json.loads(response.content)
            profile = Profile.objects.get(pk=js["profile_id"])

            original_profile = self.user.profile

            profile.p_address1 = original_profile.p_address1 or self.address1
            profile.p_address2 = original_profile.p_address2 or self.address2
            profile.p_state = original_profile.p_state or self.state
            profile.p_zip = original_profile.p_zip or self.zipcode
            profile.p_city = original_profile.p_city or self.city
            profile.p_country = original_profile.p_country or self.country
            profile.is_international = original_profile.is_international
            profile.signed_artist_agreement = True
            profile.signed_new_artist_agreement = True
            profile.signed_new_tc_aggreement = True

        return (profile, exists)

    def add_visual(self, profile, visual):
        "Process the visual for the given profile"
        logger.debug("ADD VISUAL: %s", visual)

        factory = RequestFactory()

        request = factory.post("/my-account/photos-ajax/")
        request.user = self.user

        f = File(open(visual, "rb"))
        request.FILES["photo"] = f

        response = accviews.upload_photos_ajax(request)

        if response.status_code == 200:
            logger.info("Saved artist visual: %s - %s", profile, visual)
        else:
            raise SaveArtistVisualError(
                "Failed to save artist page: {!r} - {!r}".format(profile, visual)
            )

    def set_primary_photo(self, profile):
        "Gets a list of uploaded visuals and sets the first one"
        logger.debug("SETTING PRIMARY PHOTO: %s", profile)

    def add_single(self, profile, singlepath):
        "Process the individual song"
        logger.debug("ADD SINGLE: %s", singlepath)

        if register_and_upload_song(self.user, singlepath):
            logger.info("UPLOADED SONG %s TO S3", singlepath)
        else:
            logger.error("FAILED UPLOADING SONG %s TO S3", singlepath)

    def add_album(self, profile, albumpath, albumname):
        "Create album"
        albumname = albumname.strip()

        # Don't need to use the view here
        try:
            album = Album.objects.get(profile=self.user.person.view, title=albumname)
            logger.warn("ALBUM ALREADY EXISTS %s", album)
        except Album.DoesNotExist:
            logger.debug("ADDING ALBUM: %s", albumpath)
            album = Album(
                profile=self.user.person.view, title=albumname, download_type="normal"
            )
            album.save()
        files = []
        for f in AUDIO_FORMATS + IMAGE_FORMATS:
            files.extend(glob.glob("{}/*.{}".format(albumpath, f)))
        for f in sorted(os.listdir(albumpath)):
            fpath = os.path.join(albumpath, f)
            if f.split(".")[-1] in AUDIO_FORMATS:
                logger.debug("PROCESSING ALBUM SONG: %s", f)
                if register_and_upload_song(self.user, fpath, album.id):
                    logger.info("UPLOADED SONG %s TO S3", fpath)
                else:
                    logger.error("FAILED UPLOADING SONG %s TO S3", fpath)
            elif f.split(".")[-1] in IMAGE_FORMATS:
                # upload album art
                logger.info("ADDING ALBUM ART %s", fpath)
                if not self.add_album_art(album, fpath):
                    logger.info("ERROR ADDING ALBUM ART %s", fpath)

    def add_album_art(self, album, visual):
        factory = RequestFactory()
        data = dict(albumid=album.id,)
        request = factory.post("/upload-album-cover/", data)
        request.user = self.user

        f = File(open(visual, "rb"))
        request.FILES["cover_file"] = f

        response = mediaviews.album_cover_ajax(request)

        return response.status_code == 200

    def process(self):
        for pagedir in os.listdir(self.directory):
            # top level is for profiles
            pagepath = os.path.join(self.directory, pagedir)
            # Ignore directories starting with _
            if not pagedir.startswith("_") and os.path.isdir(pagepath):
                logger.info("ARTIST: %s", pagedir)
                # Create the top level page
                profile, exists = self.add_page(pagedir)
                # Set the current view so all other files get attached to this profile
                self.set_view(profile)
                for eldir in os.listdir(pagepath):
                    elpath = os.path.join(pagepath, eldir)
                    if os.path.isfile(elpath):
                        if elpath.split(".")[-1] in IMAGE_FORMATS:
                            if not exists:
                                visual = self.add_visual(profile, elpath)
                        else:
                            logger.warn("%s file is not supported", elpath)
                    else:
                        # its a directory
                        if eldir == "albums":
                            for albumdir in os.listdir(elpath):
                                albumpath = os.path.join(elpath, albumdir)
                                if os.path.isdir(albumpath):
                                    album = self.add_album(profile, albumpath, albumdir)
                        elif eldir == "singles":
                            for singledir in os.listdir(elpath):
                                singlepath = os.path.join(elpath, singledir)
                                if os.path.isfile(singlepath):
                                    if singledir.split(".")[-1] in AUDIO_FORMATS:
                                        single = self.add_single(profile, singlepath)
                                    else:
                                        logger.debug(
                                            "file is not supported %s", singlepath
                                        )
                if not exists:
                    self.set_primary_photo(profile)


class Command(BaseCommand):
    help = "Imports media in bulk for the user specified from the directory specified"

    option_list = BaseCommand.option_list + (
        make_option(
            "--userid",
            action="store",
            dest="userid",
            help="Specify the userid of start the import process for",
        ),
        make_option(
            "--directory",
            action="store",
            dest="directory",
            help="Directory from which to start the import process",
        ),
        make_option(
            "--catalog",
            action="store",
            dest="catalog",
            help="Path to the catalog in the format Artist | Song | ISRC | Album | UPC/EAN",
        ),
        make_option(
            "--genre", action="store", dest="genre", help="Genre of the music submitted"
        ),
        make_option("--address1", action="store", dest="address1", default=None),
        make_option("--address2", action="store", dest="address2", default=None),
        make_option("--state", action="store", dest="state", default=None),
        make_option("--zipcode", action="store", dest="zipcode", default=None),
        make_option("--city", action="store", dest="city", default=None),
        make_option("--country", action="store", dest="country", default=None),
    )

    def handle(self, *args, **options):
        """Import media in bulk"""
        # ./manage.py bulk_import --catalog catalog.csv --directory ./rnb/rnb/ --userid 4900 --genre Rnb --address1 Music World Entertainment --address2 5120 Woodway Dr. --state TX --zipcode 77056 --city Houston  --country United States of America
        # importer = BulkImporter(4143, './rnb/rnb/', 'catalog.csv', 'Rnb')
        # importer.process()
        importer = BulkImporter(
            user_id=int(options["userid"]),
            directory=options["directory"],
            catalog=options["catalog"],
            genre=options["genre"],
            address1=options.get("address1"),
            address2=options.get("address2"),
            state=options.get("state"),
            zipcode=options.get("zipcode"),
            city=options.get("city"),
            country=options.get("country"),
        )
        importer.process()
