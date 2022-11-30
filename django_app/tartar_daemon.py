import os
import time
import logging
from functools import reduce

import django

django.setup()

from django.conf import settings
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from accounts.models import StatusUpdate
from media.models import Song
from the_hearo_team import send_msg
from tartar import ThriftShop
from infrared import Context


logger = logging.getLogger("tartar.puller")


class TarTarChanges:
    def run(self):
        logger.info("looking for tartar changes...")
        while True:
            self.pull()
            time.sleep(5)

    def pull(self):
        ts = ThriftShop(Context(settings.CONFIG))
        changes = ts.getupdates()

        logger.debug("checking...")

        # Don't log or do anything if there were no changes
        if reduce(lambda a, b: a + len(b[1]), list(changes.items()), 0) == 0:
            return

        logger.debug("changes detected")
        logger.debug(changes)
        for changetype in changes:
            for change in changes[changetype]:
                logger.info(change)
                try:
                    self.change_song_status(changetype, **change)
                except Exception as e:
                    logger.error(str(e))
                else:
                    ts.removeupdated(change)

    def change_song_status(self, status, id, msg="", length=None, **obj):
        songid = id
        connection.connect()
        logger.info("Updating Songid %s (SET %s with PARAMS: %s)", songid, status, obj)
        try:
            song = Song.objects.get(id=songid)
        except ObjectDoesNotExist:
            logger.error("Song matching id %s does not exist", songid)
            return
        else:
            logger.info("Songid %s (SET %s with PARAMS: %s)", songid, status, obj)

        p = song.profile

        if status == "online":
            if not song.online:
                song.online = True
                song.save()

                try:
                    send_msg(
                        p,
                        "Tune.fm upload success",
                        "{} has been processed!".format(song.title),
                    )
                except Exception as e:
                    logger.error(e, exc_info=True)

            if song.visible and song.processing:
                # Make an automated status update for them.
                status = "Uploaded a song, " + song.title
                status_update = StatusUpdate.objects.create(
                    status=status,
                    profile_id=p.id,
                    object_id=song.id,
                    content_type=ContentType.objects.get_for_model(Song),
                )
                p.updates.add(status_update)
                p.save()
                logger.info("Created status update for song upload")
            song.processing = False
            song.length = length
            logger.info("SONG NOW ONLINE")
            song.save()

        elif status == "offline":
            logger.info(
                "Song %s with id %d changed status to offline", song.title, song.id
            )
            song.online = False
            song.save()
        elif status == "uploaderr":
            # if we dont give the user a message, dont tell them there was an
            # error message
            if msg:
                logger.exception(
                    "Failed to upload the song %s (id: %s). The following message was received: %s",
                    song.title,
                    song.id,
                    msg,
                )
            else:
                logger.exception(
                    "Failed to upload the song %s (id: %s). An unknown error occurred",
                    song.title,
                    song.id,
                )
            song.state_info = msg
            song.save()
        connection.close()


def main():
    puller = TarTarChanges()
    puller.run()


if __name__ == "__main__":
    logging.info("Daemon is starting with %s", os.getenv("DJANGO_SETTINGS_MODULE"))
    if bool(int(os.environ.setdefault("IPDB_DEBUG", "0"))):
        from ipdb import launch_ipdb_on_exception

        with launch_ipdb_on_exception():
            main()
    else:
        main()
