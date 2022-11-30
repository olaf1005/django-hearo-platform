import time

from infrared import HearoS3

from .thriftshop import ThriftShop


class GetLucky(ThriftShop):
    def image_upload(self, imageid, path, userid, target):
        """
        uploads an image file directly from the hearo server
        to the s3 bucket.
        it then registers the file with TarTar
        """

        target = target.lower()
        if target not in ("profile", "album", "banner", "normal"):
            raise Exception("target needs to be profile, album or banner")

        hs3 = HearoS3(self.context, None)
        ret = hs3.upload("dripdrop", path)

        return self.image_register(imageid, ret["key"], userid, target)

    def image_register(self, imageid, filename, userid, target):
        """
        registers the image with TarTar
        """
        obj = {
            "imageid": imageid,
            "original": filename,
            "user": userid,
            "marked": 0,
            "images": {},
            "time_reg": time.time(),
            "time_upl": None,
            "time_pro": None,
            "time_rea": None,
            "target": target,
            "deleted": 0,
        }

        ret = self.db.table("images").insert(obj).run(self.conn)
        # print ret
        return ret["inserted"] == 1

    def image_get(self, imageid, index):

        ret = self.db.table("images").get(imageid).run(self.conn)

        if ret is None:
            return {"status": "does not exist"}
        elif ret.get("status", "fake") == "fake":
            return {"status": "offline"}
        elif not ret["status"] == "online":
            return {"status": "offline"}
        elif ret["status"] == "deleted" or ret.get("deleted", False) is True:
            return {"status": "deleted"}
        else:
            return {"status": "online", "url": ret["images"][index]}

    def image_url(self, imageid, index):
        """
        fetches the url
        """
        ret = self.image_get(imageid, index)
        return ret.get("url", None)

    def image_delete(self, imageid):
        """
        marks the file for deletion.

        returns True if the file was successfully deleted.
        False Otherwise.
        """
        ret = self.db.table("images").get(imageid).update({"deleted": 1}).run(self.conn)
        # print ret
        return ret["replaced"] == 1 or ret["unchanged"] == 1

    def getupdates(self):
        """
        returns a dict of changes {online, offline, uploaderr} as dicts

        This can be error prone depending on the order of duplicate songids in the changes table
        """

        ret = {"online": [], "error": []}

        entries = self.db.table("images_changes").limit(100).run(self.conn)

        for e in entries:

            if e["status"] == 1:
                obj = {"id": e["imageid"], "url": e["url"]}
                ret["online"].append(obj)

            entries = (
                self.db.table("images_changes")
                .get(e["downloadid"])
                .delete()
                .run(self.conn)
            )

        return ret
