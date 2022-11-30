# -*- coding: utf-8 -*-
"""
Reprocesses broken or missing songs.

First we check rethinkdb for the streaming_url, if thats
missing, we use the song.keyword and song.file info to
attempt tracking the file on s3 using the previous version of the
digest used to determing the filename (The new version adds an extension so
that needs to be removed).

If the file is on s3, we can reprocess the song.

Tracking the song on cloudfiles itself does not work since the actual
url is a random hash.

./manage.py reprocess_missed_songs
"""
import os
import logging

from django.core.management.base import BaseCommand
from django.test.client import RequestFactory

from accounts.models import Person
from media.models import Song
from media import views as mediaviews

from infrared import Context
from infrared import HearoS3, HearoCloudFiles
from tartar import CallMeMaybe


logger = logging.getLogger(__name__)

context = os.environ.get("TARTAR_CONFIG")

hearos3 = HearoS3(context)
hearocloudfiles = HearoCloudFiles(context)


def check_file_on_s3_failures(song):
    # Some containers use a prefix for the file name
    logger.info("CHECKING IF %s IS ON S3 FAILURES", song)
    if song.keyword:
        logger.info("CHECKING KEYWORD %s", song.keyword)
        if hearos3.exists("failures", "{}{}".format("failed_", song.keyword)):
            logger.info("FOUND!")
            return ("failures", "{}{}".format("failed_", song.keyword))
    else:
        sig = CallMeMaybe.generate_signature(song.title, "audio/wav")
        keyword = sig["url"].split("https://hearo_uploadedsongs.s3.amazonaws.com/")[1]
        logger.debug("CHECKING WITH SIG KEYWORD %s", keyword)
        if hearos3.exists("failures", keyword):
            logger.info("FOUND!")
            return ("failures", "{}{}".format("failed_", keyword))
        if hearos3.exists("failures", "failed_{}".format(keyword)):
            logger.info("FOUND!")
            return ("failures", "failed_{}".format(keyword))
    logger.error("NOT FOUND!")
    return None


def check_file_on_s3_uploaded(song):
    # Some containers use a prefix for the file name
    logger.info("CHECKING IF SONG %s IS ON S3 UPLOADED", song)
    if song.keyword:
        logger.debug("CHECKING KEYWORD %s", song.keyword)
        if hearos3.exists("dripdrop", song.keyword):
            logger.info("FOUND!")
            return ("dripdrop", song.keyword)
    else:
        sig = CallMeMaybe.generate_signature(song.title, "audio/wav")
        keyword = sig["url"].split("https://hearo_uploadedsongs.s3.amazonaws.com/")[1]
        logger.debug("CHECKING WITH SIG KEYWORD %s", keyword)
        if hearos3.exists("dripdrop", keyword):
            logger.info("FOUND!")
            return ("dripdrop", keyword)
    logger.warn("NOT FOUND!")
    return None


def reprocess_song(song):
    logger.info("REPROCESSING SONG %s", song)

    factory = RequestFactory()
    data = dict(id=song.id)
    request = factory.post("/cmm-register/", data)
    if song.profile.user is None:
        logger.error("SONG %s PROFILE IS NOT ATTACHED TO A USER", song.id)
        return False
    else:
        user = song.profile.user
        try:
            person = user.person
        except Person.DoesNotExist:
            logger.error("NO PERSON FOR %s", user)
            return False
        user.person.view = song.profile
        user.person.save()
        request.user = user

        response = mediaviews.cmm_register(request)
        if response.status_code == 200:
            logger.info("Successfully uploaded and registered song %s", song.keyword)
        else:
            logger.error("Failed to uploaded and registered song %s", song.keyword)
        return True


def upload_failed_song_to_uploads(song, keyword):
    newkey = "{}.wav".format(keyword.lstrip("failed_"))
    hearos3.copy_object("failures", keyword, "dripdrop", newkey)
    song.keyword = newkey
    song.save()


def copy_dripdrop_to_uploads(song, keyword):
    newkey = "{}.wav".format(keyword)
    hearos3.copy_object("dripdrop", keyword, "dripdrop", newkey)
    song.keyword = newkey
    song.save()


class Command(BaseCommand):
    help = "Reprocesses songs not successfully uploaded"

    def handle(self, *args, **options):
        logger.info(self.help)

        broken_songs = []
        for song in Song.objects.all():
            if not song.streaming_url():
                broken_songs.append(song)

        logger.info("%s SONGS BROKEN", len(broken_songs))

        songs_not_found = []
        songs_found = []

        for song in broken_songs:
            # Check if song is on s3
            # we check on the appropriate container
            # defined in prod.config
            location = check_file_on_s3_uploaded(song)
            if not location:
                location = check_file_on_s3_failures(song)
            if location:
                logger.info("FILE FOUND ON %s - %s", location[0], location[1])
                songs_found.append((song, location))
                if location[0] == "failures":
                    upload_failed_song_to_uploads(song, location[1])
                elif location[0] == "dripdrop":
                    copy_dripdrop_to_uploads(song, location[1])
                reprocess_song(song)
            else:
                logger.info("FILE WAS NOT FOUND FOR SONG %s", song)
                songs_not_found.append(song)

        logger.info("%s SONGS REPROCESSED", len(songs_found))
        logger.info("%s SONGS NOT FOUND", len(songs_not_found))
