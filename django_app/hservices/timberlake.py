import logging
import os
import uuid
import shutil
import time
import datetime

from . import audioutils

from .hservice import HearoService
from tartar import ThriftShop
from infrared import Context, HearoCloudFiles


logger = logging.getLogger("tartar.hservice.timberlake")


class Timberlake(HearoService):
    """
        Timberlake is a class that helps process download requests
    """

    def __init__(self, context=None):
        """
            init() constructor
        """
        super().__init__("Timberlake", context)
        self.go = True

    def run_test(self, package):
        """
            A method to be used only for initial testing ... do not use!
        """
        self.package = package
        self.ts = ThriftShop(self.context)
        self.download()

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
        logger.info("timberlake starting..")

        self.ts = ThriftShop(self.context)

        while self.go:
            # Need to raise the exception if IPBD_DEBUG is enabled
            if bool(int(os.environ.setdefault("IPDB_DEBUG", "0"))):
                work = self.getwork()
                if work == 0 or work == -1:
                    time.sleep(5)
                    continue

                self.download()
            else:
                try:
                    work = self.getwork()
                    if work == 0 or work == -1:
                        time.sleep(5)
                        continue

                    self.download()
                except Exception as e:
                    logger.exception(e)

        logger.error("timberlake cleanly shutdown")

    def download(self):
        """
            Downloads songs, converts songs, applies metadata
            zips and uploads the archive

            input: none
            outputs: True if success, False or exception otherwise

            loops throw a package dict
                downloads songs into their correct folders
                converts songs, renames them and then applies metadata
                zips everything together
                uploads the zip file

            SIDE EFFECTS:
                - Does a lot things in mixingbowl directory
                - take care not to be messing around in here
        """

        logger.debug("package found ... building directories")
        # build two temp directories
        dir_origin = (
            self.context.getContext()["basepath"]
            + "/mixingbowl/d_o_"
            + str(uuid.uuid4())
        )
        dir_target = (
            self.context.getContext()["basepath"]
            + "/mixingbowl/d_t_"
            + str(uuid.uuid4())
        )
        os.mkdir(dir_origin)
        os.mkdir(dir_target)

        formats = self.context.getService("formats")
        for f in self.package["folders"]:
            logger.info(f)

            opath = dir_origin + "/" + f["name"]
            fpath = dir_target + "/" + f["name"]

            os.mkdir(opath)
            os.mkdir(fpath)

            for s in f["songs"]:

                privkey = self.ts.getkey(s["songid"], ThriftShop.Song)
                logger.debug("key found")

                cf = HearoCloudFiles(self.context)
                filepath = "{}/{}".format(opath, privkey)
                cf.download("ironcurtain", privkey, filepath)
                logger.debug("file downloaded")

                original = audiotools.open(filepath)

                newpath = "{}/{}{}".format(
                    fpath,
                    s["track_name"],
                    formats["formats"][s["targetformat"].lower()]["ext"],
                )

                original.convert(
                    newpath, audioutils.string_to_format(s["targetformat"])
                )
                logger.debug("file converted")

                md = original.get_metadata()

                for m in s.keys():
                    if m in ("songid", "targetformat"):
                        pass
                    setattr(md, m, s[m])

                newfile = audiotools.open(newpath)
                newfile.set_metadata(md)

                logger.debug("meta set")

            # completed all folders ... maybe we can delete origin folders here
            shutil.rmtree(opath)
            # logger.info("deleted local file")

        # zip starts here
        now = datetime.datetime.now()
        zipname = "{}_hearofm_download_{}".format(
            self.zipuser, now.strftime("%m%d%Y_%H%M_%f")
        )
        zippath = "{}/mixingbowl/{}".format(
            self.context.getContext()["basepath"], zipname
        )

        shutil.make_archive(zippath, "zip", root_dir=dir_target, logger=logger)

        logger.debug("zipped everything")

        zippath = zippath + ".zip"
        zipname = zipname + ".zip"

        # upload files
        cf = HearoCloudFiles(self.context)
        (key, url) = cf.reUpload("zips", zipname, zippath)

        logger.debug("uploaded")

        # Delete all old files
        shutil.rmtree(dir_origin)
        shutil.rmtree(dir_target)
        os.remove(zippath)
        logger.debug("files cleared")

        self.db.table("downloads").get(self.downid).update(
            {"finished": 1, "url": url, "key": key}
        ).run(self.conn)
        self.db.table("downloads_lock").filter({"lockon": self.downid}).delete().run(
            self.conn
        )

        chg = {"downloadid": self.downid, "status": 1, "url": url}
        self.db.table("downloads_changes").insert(chg).run(self.conn)

    def getwork(self):
        """
            make sure that this process is the only process working on a package
        """

        cnt = self.db.table("downloads").filter({"marked": 0}).count().run(self.conn)

        # if we have no pending songs
        # we skip back to the top of the loop
        if cnt == 0:
            logger.debug("approx %s files in queue", cnt)
            return 0

        logger.info("approx %s files in queue", cnt)

        ret = self.db.table("downloads").filter({"marked": 0}).run(self.conn)

        # make sure we are the only one's working on it.
        item = None
        for i in ret:
            _id = i["downloadid"]
            t = self.db.table("downloads_lock").insert({"lockon": _id}).run(self.conn)
            try:
                if t["errors"] > 0:
                    logger.info("missed a lock on download %s", _id)
                else:
                    item = i
                    break
            except KeyError:
                item = i
                break

        # we missed every song lock, so we need to bounce back to the top of the loop
        if item is None:
            logger.info("missed every download lock")
            return -1

        # update process table
        self.downid = item["downloadid"]
        self.db.table("downloads").get(self.downid).update(
            {"marked": 1, "status": 10}
        ).run(self.conn)

        self.package = item["package"]
        self.zipuser = item.get("user", "hearouser")
        logger.info("working on download id: %s", self.downid)

        return 1
