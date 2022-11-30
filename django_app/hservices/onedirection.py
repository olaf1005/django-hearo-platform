# onedirection.py
#
# Note: Once a file fails to process, it will not reprocess until the key in
# the rethinkdb 'in_process' table gets removed. Once cleared, it will
# reprocess
#
# OneDirection is a background daemon that waits for newly uploaded files
# to convert and send to the CDN / Cloudfiles
#
# As a file is uploaded to the cloudfiles via TempDir,
# it should be registered with the database (remotely) via CallMeMaybe.py
#
# OneDirection waits for a registered entry to become ready, it will then
# lock the entry and begin to process it.
#
# It first downloads the file from S3 and validates it
#
# Then it converts the file to a master format (flac)
#
# Then it converts the master to an MP3 (128) for streaming and a MP3 (320)
# for downloading
#
# It then uploads these files back into rackspace and registers their locations
# with the database.
#
# It should be deployed alongside a local rethinkdb song repo
#
# At this point, there is no distributed database admin included in
# onedirection.py
#
#

import logging
import uuid
import time
import os
import shutil

import sox
import audiotools

from .hservice import HearoService  # also imports rethinkdb

from infrared import Context
from infrared import HearoS3, HearoCloudFiles

from . import onedirectionerrorstrings


logger = logging.getLogger("tartar.hservice.one_direction")

errorstrings = onedirectionerrorstrings.error_strings


class OneDirection(HearoService):
    """
    OneDirection is a service that
    transfers and converts uploaded files
    to hearo's CDN
    """

    def __init__(self, context=None, PROD=False):
        super().__init__("OneDirection", context)

        self.PROD = PROD

        self.total_size = 0
        self.files_ahead = 0

        # should the process keep running?
        self.go = True

    def shutdown(self):
        "async call"

        self.go = False
        logger.info("KILL REQUESTED")

    def run(self):
        "main loop for daemon"
        while self.go:
            try:
                self.hello()

                # self.cleanup()

                self.error_string = "unknown"

                self.checkonuploads()
                work = self.getwork()

                if work in [0, -1]:
                    time.sleep(5)
                    continue

                if self.downloadandwaits3() <= 0:
                    self.error()
                    continue

                if self.validate() <= 0 or self.convert() <= 0:
                    self.error()
                    continue

                self.reUpload()

                # finally, get rid of the local and s3 files
                self.delete_uploaded()

            except Exception as e:
                logger.exception(e)

        logger.info("OneDirection has shutdown")

    def checkonuploads(self):
        """
        check to see if the a file associated with the registered S3
        Key has finally uploaded

        do this by looping through all registered unmarked entries
        ir the table

        if it is, then mark it ready for processing
        """
        ret = self.db.table("process").filter({"marked": 0}).run(self.conn)

        s3 = HearoS3(self.context)

        logger.debug("checking on uploads")

        for r in ret:
            key = r["filename"]
            logger.debug("checking s3 for key %s", key)
            if s3.exists("dripdrop", key):
                logger.info("found: %s", key)

                size = s3.size("dripdrop", key)

                self.total_size = self.total_size + size

                obj = {
                    "marked": 1,
                    "percent": 10,
                    "bytesahead": self.total_size,
                    "bytestotal": self.total_size,
                    "filesahead": self.files_ahead,
                    "markedat": int(time.time()),
                    "size": size,
                }

                self.files_ahead += 1

                # mark it
                self.db.table("process").get(r["songid"]).update(obj).run(self.conn)

    def getwork(self):
        """
        gets the id of the next file
        to pull from the dropoff cloudfiles


        To ensure that we are the only process working on a particular file,
        we create a new entry in the distributed database
        """

        cnt = self.db.table("process").filter({"marked": 1}).count().run(self.conn)

        # if we have no pending songs
        # we skip back to the top of the loop
        if cnt == 0:
            logger.debug("approx %s files in queue", cnt)
            # reset counters
            self.files_ahead = 0
            self.total_size = 0
            return 0

        logger.info("approx %s", cnt)

        # markedat ensures that we order by when the file finshed uploading,
        # not by when the songid, or row id
        ret = (
            self.db.table("process")
            .order_by("markedat")
            .filter({"marked": 1})
            .run(self.conn)
        )

        # make sure we are the only one's working on it.
        item = None
        for i in ret:
            songid = i["songid"]
            key = i["filename"]

            if key is None or key == "":
                logger.info("empty s3 key for songid: %s", songid)
                self.db.table("process").delete(songid).run(self.conn)
                continue

            t = self.db.table("in_process").insert({"songid": songid}).run(self.conn)

            try:
                if t["errors"] > 0:
                    logger.error(t["first_error"])
                    logger.info("missed a lock on song %s s3 filename %s", songid, key)
                else:
                    item = i
                    break
            except KeyError:
                item = i
                break

        # we missed every song lock, so we need to bounce back to the top of the loop
        if item is None:
            logger.info("missed every song lock ...")
            return -1

        # update process table
        self.db.table("process").get(songid).update(
            {"marked": 1, "status": 10, "percent": 70}
        ).run(self.conn)
        self.songid = songid
        self.song_filename = item["filename"]

        # if self.song_filename == "" or self.song_filename == None:
        #    logger.info("no key given")
        #    return -1

        # adjust progress percentages
        self.db.table("process").filter({"marked": 1, "percent": 10}).update(
            lambda x: {"bytesahead": x["bytesahead"] - item["size"]}
        ).run(self.conn)
        self.total_size = self.total_size - item["size"]
        self.db.table("process").filter({"marked": 1, "percent": 10}).update(
            lambda x: {"filesahead": x["filesahead"] - 1}
        ).run(self.conn)
        self.files_ahead = self.files_ahead - 1

        logger.info("working on song id: %s s3 key: %s", songid, self.song_filename)

        return 1

    def downloadandwaits3(self):
        """
        downloads the file from s3
        creates the temp dir
        waits for download to complete
        """

        logger.info("started downloading s3 key %s", self.song_filename)

        s3 = HearoS3(self.context)

        self.path = (
            self.context.getContext()["basepath"]
            + "/mixingbowl/"
            + str(uuid.uuid4())
            + "/"
        )
        os.mkdir(self.path)
        self.filename = self.path + self.song_filename

        # s3 key             #path
        s3.download("dripdrop", self.song_filename, self.filename)

        self.db.table("process").get(self.songid).update({"percent": 80}).run(self.conn)

        return 1

    def validate(self):
        """
        validates the file
        """
        try:
            self.original = audiotools.open(self.filename)
        except audiotools.InvalidFile as e:
            self.error_string = "invalid"
            logger.error("caught failure - invalid file: %s", e)
            return -1
        except audiotools.UnsupportedFile as e:
            self.error_string = "unsupported"
            logger.error("caught failure - unsupported filetype: %s", e)
            return -1
        except IOError as e:
            self.error_string = "internal"
            logger.error("caught failure - io error: %s", e)
            return -1

        logger.info("opened original %s", self.filename)

        try:
            self.original.verify()
            self.secs = int(self.original.seconds_length())
        except audiotools.InvalidFile as e:
            original_err = e
            try:
                logger.info("invalid file, attempting fix on - %s", self.filename)
                tfm = sox.Transformer()
                fname, ext = os.path.splitext(self.filename)
                new_filename = "{}_fixed{}".format(fname, ext)
                tfm.build(self.filename, new_filename)
                os.rename(new_filename, self.filename)
                self.original = audiotools.open(self.filename)
                self.original.verify()
                self.secs = int(self.original.seconds_length())
            except Exception as e:
                self.error_string = "invalid"
                logger.error(
                    "caught failure - invalid file %s, fix failed %s",
                    str(original_err),
                    e,
                )
                return -1
        except ValueError as e:
            self.error_string = "invalid"
            logger.error("caught failure, error: %s", e)
            return -1

        self.db.table("process").get(self.songid).update({"percent": 85}).run(self.conn)

        logger.info("validated original")

        if not self.original.lossless():
            self.error_string = "lossy"
            logger.info("not lossless")
            return -1

        return 1

    def convert(self):
        """
            Converts downloaded file to a master flac format
            Converts master flac to a streaming mp3 format
        """

        logger.info("converting...")
        # convert to master.flac
        try:
            self.master = self.original.convert(
                self.path + self.song_filename + "_master.flac", audiotools.FlacAudio
            )
        except audiotools.EncodingError:
            logger.info("caught failure - master encoding error")
            return -1

        logger.info("master encoded")

        # convert to streaming mp3.get_object
        try:
            self.master.convert(
                "{}{}_stream.mp3".format(self.path, self.song_filename),
                audiotools.MP3Audio,
            )
        except audiotools.EncodingError:
            logger.info("caught failure - streaming encoding error")
            return -1

        logger.info("streaming encoded")

        self.db.table("process").get(self.songid).update({"percent": 90}).run(self.conn)

        return 1

    def reUpload(self):
        """
            upload master file
            upload streaming file
        """

        cf = HearoCloudFiles(self.context)

        path = self.path + self.song_filename + "_stream.mp3"
        (pubkey, puburl) = cf.upload("publichouse", path, suffix=".mp3")
        logger.info("uploaded: streaming")

        path = self.path + self.song_filename + "_master.flac"
        (prikey, _) = cf.upload("ironcurtain", path, suffix=".flac")
        logger.info("uploaded: master")

        obj = {
            "songid": self.songid,
            "publicurl": puburl,
            "pubkey": pubkey,
            "prikey": prikey,
            "streamurl": "",
            "length": self.secs,
            "time": int(time.time()),
        }

        logger.info(str(obj))

        chg = {"songid": self.songid, "status": 1, "info": puburl}

        # success!

        # add to songs processed
        self.db.table("songs").insert(obj).run(self.conn)
        self.db.table("changes").insert(chg).run(self.conn)

        # update completion percent
        self.db.table("process").get(self.songid).update({"percent": 96}).run(self.conn)

        # remove from procesing tables
        self.db.table("process").get(self.songid).delete().run(self.conn)
        self.db.table("in_process").get(self.songid).delete().run(self.conn)

        return 1

    def delete_uploaded(self):
        """
            delete old files in both s3 and the local filesystem
        """

        s3 = HearoS3(self.context)
        s3.delete("dripdrop", self.song_filename)
        logger.info("deleted from s3")

        # remove files from local filesystem
        shutil.rmtree(self.path)
        logger.info("deleted local file")

    def error(self):
        """
            mark current song as a failure
        """

        s3 = HearoS3(self.context)
        s3.reUpload("failures", "failed_" + self.song_filename, self.filename)

        self.delete_uploaded()

        try:
            emsg = errorstrings[self.error_string]
        except KeyError as ke:
            logger.exception(ke)
            emsg = "server error"

        chg = {"songid": self.songid, "status": -1, "info": emsg}
        self.db.table("changes").insert(chg).run(self.conn)

        fail = {
            "songid": self.songid,
            "message": emsg,
            "key": self.song_filename,
            "time": int(time.time()),
        }
        self.db.table("failures").insert(fail).run(self.conn)

        self.db.table("process").get(self.songid).delete().run(self.conn)
        self.db.table("in_process").get(self.songid).delete().run(self.conn)

        return 1


# run the app
if __name__ == "__main__":
    one = OneDirection()
    one.run()
