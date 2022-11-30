import time

from .thriftshop import ThriftShop


class GangnamStyle(ThriftShop):
    """Download manager

    -1 = does not exist
    0 = added
    1 - in process
    2 - all songs downloaded
    3 - local zipped
    4 - remote no url
    5 = ready
    6 = canceled (logic to be worked out later....

    """

    def requestdownload(self, userid, package, username="hearouser"):
        "returns packageid"

        # avoid duplications
        # packageid = str(userid) + "_" + str(packagehas(packaging)

        psecs = time.time()
        ret = (
            self.db.table("downloads")
            .insert(
                {
                    "status": 0,
                    "created": psecs,
                    "package": package,
                    "url": "",
                    "errorstring": "",
                    "user": userid,
                    "marked": 0,
                    "finished": 0,
                    "key": "",
                    "canceled": False,
                    "username": username,
                }
            )
            .run(self.conn)
        )

        return ret["generated_keys"][0]

    def status(self, packageid):
        """
        check the status of download request on tartar
        returns status code

        -1 means the package id does not exist
        """

        ret = self.db.table("downloads").get(packageid).run(self.conn)

        if ret is None:
            return -1
        else:
            return ret["status"]

    def is_ready(self, packageid):
        """
        checks if the the package is ready and it is on the cdn
        """
        return not self.geturl(packageid) is None

    def geturl(self, packageid):
        """
        returns the url of a completed package
        """

        ret = self.db.table("downloads").get(packageid).run(self.conn)

        # double check
        if ret is None:
            return None

        # make sure the user ids match
        # This validation should be done on hearo too
        # :p
        # if userid != ret['user']:
        # s    return None

        # has the download been canceled?
        if ret["status"] == 6 or ret.get("cancel", False):
            return None

        return ret["url"]

    def canceldownload(self, packageid):
        """
        NOT CURRENTLY SUPPORTED
        """
        ret = (
            self.db.table("downloads")
            .get(packageid, "downloadid")
            .update({"status": 6, "cancel": True})
            .run(self.conn)
        )

        return ret

    def getupdates(self):
        """
        returns a dict of changes {online, offline, uploaderr} as dicts

        This can be error prone depending on the order of duplicate songids in the changes table
        """

        ret = {"online": [], "error": []}

        entries = self.db.table("downloads_changes").limit(100).run(self.conn)

        for e in entries:

            if e["status"] == 1:
                obj = {"id": e["downloadid"], "url": e["url"]}
                ret["online"].append(obj)

            entries = (
                self.db.table("downloads_changes")
                .get(e["downloadid"])
                .delete()
                .run(self.conn)
            )

        return ret

    # TODO: this isn't used yet, but would need to be if downloads are renabled
    # since changes at the moment are removed in the above getupdates method
    # which if down stream there is an error, the update will not be acknowledged
    # def removeupdated(self, update):
    #     self.db.table('downloads_changes').get(update["id"]).delete().run(self.conn)
