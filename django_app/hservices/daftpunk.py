import logging
import os
import uuid
import time
import math

from PIL import Image

from tartar import ThriftShop
from infrared import HearoCloudFiles
from infrared import HearoS3

from .hservice import HearoService


logger = logging.getLogger("tartar.hservices.daftpunk")


class DaftPunk(HearoService):
    """
        DaftPunk is an image manipulation and management
        libary
    """

    def __init__(self, context=None):
        """
            init() constructor
        """
        super().__init__("DaftPunk", context)
        self.ts = ThriftShop(self.context)
        self.go = True

    def shutdown(self):
        """
            sets the shutdown flag for a clean shutdown
        """
        self.go = False
        logger.error("Timberlake - kill requested")

    def run(self):
        """

            method run()
            inputs: None
            outputs: None

            throws Exceptions:
                TBD


            Main loop for Timberlake
        """

        while self.go:
            try:
                self.checkonuploads()
                work = self.getwork()
                if work in [0, -1]:
                    time.sleep(5)
                    continue

                if self.downloadandwaits3() is False:
                    self.error()
                    continue

                if self.manipulate() is False:
                    self.error()
                    continue

                self.reUpload()

            except Exception as e:
                logger.exception(e)

        logger.info("DaftPunk shutdown")

    def checkonuploads(self):
        """
        check to see if the a file associated with the registered S3
        Key has finally uploaded
        do this by looping through all registered unmarked entries-$
        in the table
        if it is, then mark it ready for processing
        """
        ret = self.db.table("images").filter({"marked": 0}).run(self.conn)
        s3 = HearoS3(self.context)
        logger.debug("checking on uploaded images")

        x = 0
        y = 0
        for r in ret:
            key = r["original"]
            logger.debug("checking s3 for key %s", key)
            if s3.exists("dripdrop", key):
                logger.info("found: %s", key)
                obj = {"marked": 1, "time_upl": time.time()}
                # mark it
                self.db.table("images").get(r["imageid"]).update(obj).run(self.conn)
                y = y + 1
            x = x + 1

        logger.debug("done checking on uploaded images %s/%s", y, x)

    def getwork(self):
        """
            make sure that this process is the only process working on a package
        """

        cnt = self.db.table("images").filter({"marked": 1}).count().run(self.conn)

        # if we have no pending songs
        # we skip back to the top of the loop
        if cnt == 0:
            logger.debug("approx %s files in queue", cnt)
            return 0

        logger.info("approx %s files in queue", cnt)

        ret = self.db.table("images").filter({"marked": 1}).run(self.conn)

        # make sure we are the only one's working on it.
        item = None
        for i in ret:
            _id = i["imageid"]
            t = self.db.table("images_lock").insert({"lockon": _id}).run(self.conn)
            try:
                if t["errors"] > 0:
                    logger.info("missed a lock on image %s", _id)
                else:
                    item = i
                    break
            except KeyError:
                item = i
                break

        # we missed every song lock, so we need to bounce back to the top of the loop
        if item is None:
            logger.info("missed every image lock")
            return -1

        # get and set globals
        self.imageid = item["imageid"]
        self.image_filename = item["filename"]
        self.target = item["target"]

        # update process table
        self.db.table("images").get(self.imageid).update(
            {"marked": 1, "status": 10, "time_pro": time.time()}
        ).run(self.conn)

        # self.package = item["package"]
        # self.zipuser = item.get("user", "hearouser")
        logger.info("working on image id: %s", self.imageid)

        return 1

    def downloadandwaits3(self):
        """
            downloads the file from s3
            creates the temp dir
            waits for download to complete
        """

        logger.info("started downloading s3 key %s", self.image_filename)

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

        return True

    def manipulate(self):
        """
            create the modified images

        """

        self.suffixes = []

        # orignal file load and info
        img = Image.open(self.filename)
        width, height = img.size
        if width < 4 or height < 4:
            self.error_string = "toosmall"
            return False

        # set new path variable
        newpath = self.path + self.imageid
        # save an orignal file as a jpg
        img.save(newpath + "_original.jpg")
        self.suffixes.append("original")

        if self.target in ("normal", "profile", "album"):

            scal = img.copy()
            if height > 1200:
                ratio = 1200 / height
                nwidth = math.floor(width * ratio)
                scal = scal.scale(nwidth, 1200)

            swidth, sheight = scal.size
            if swidth > 1200:
                ratio = 1200 / swidth
                nheight = math.floor(sheight * ratio)
                scal = scal.scale(1200, nheight)
            scal.save(newpath + "_scaled.jpg")
            self.suffixes.append("scaled")

            x1 = 0
            y1 = 0
            x2 = width
            y2 = height

            if width > height:
                x1 = math.floor((width - height / 2))
                x2 = x1 + height
            elif height > width:
                y1 = math.floor((height - width / 2))
                y2 = y1 + width
            crop = img.crop((x1, y1, x2, y2))

            px400 = crop.scale(400, 400)
            px400.save(newpath + "_400px.jpg")
            px300 = crop.scale(300, 300)
            px300.save(newpath + "_300px.jpg")
            px200 = crop.scale(200, 200)
            px200.save(newpath + "_200px.jpg")
            px100 = crop.scale(100, 100)
            px100.save(newpath + "_100px.jpg")
            px60 = crop.scale(60, 60)
            px60.save(newpath + "_60px.jpg")

            self.suffixes.append(["400px", "300px", "200px", "100px", "60px"])

        elif self.target == "banner":

            banner = img.scale(965, 160)
            banner.save(newpath + "_banner.jpg")

            self.suffixes.append("banner")
        return True

    def reUpload(self):
        """
            upload images to cloudfiles
        """

        cf = HearoCloudFiles(self.context)

        subimages = {}
        for x in self.suffixes:

            path = self.path + self.image_id + "_" + x + ".jpg"
            (pubkey, puburl) = cf.reUpload("images", path, suffix=".jpg")
            logger.info("uploaded: %s", x)
            subimages[x] = puburl

        obj = {"status": "online", "images": subimages, "time_rea": int(time.time())}

        logger.info(obj)

        chg = {"imageid": self.songid, "status": 1, "info": self.target}

        # success!

        self.db.table("images").get(self.imageid).update(obj).run(self.conn)
        self.db.table("images_changes").insert(chg).run(self.conn)
        # self.db.table('process').get(self.songid).delete().run(self.conn)
        self.db.table("images_lock").get(self.imageid).delete().run(self.conn)

        return 1

    def error(self):
        """
            handle errors
        """
        logger.info(self.error_string)

        obj = {"status": "failed"}
        chg = {"imageid": self.imageid, "status": -1, "info": self.error_string}

        self.db.table("images").get(self.imageid).update(obj).run(self.conn)
        self.db.table("images_changes").insert(chg).run(self.conn)
        self.db.table("images_lock").get(self.imageid).delete().run(self.conn)

        return 1


# run the app
if __name__ == "__main__":
    dp = DaftPunk()
    dp.run()
