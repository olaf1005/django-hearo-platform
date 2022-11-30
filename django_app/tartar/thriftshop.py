import json

from infrared import Context
import rethinkdb

from tartar.utils import CMMImage, CMMSong, CMMImg


class ObjNotInDB(Exception):
    pass


class FieldNotInDB(Exception):
    pass


class TableNotInDB(Exception):
    pass


class ThriftShop(object):
    "Manage Files at the end point"

    Song = CMMSong()
    # Image = CMMImage()
    # Img = CMMImage

    def __init__(self, context=None):
        """
        @param test - False to use the DB specified in the machine's context file
                    - a filename with a file to build a fake database within a dict

        """

        self.context = context
        if self.context is None:
            self.context = Context()
        (self.db, self.conn) = self.context.getDB()

    def getkey(self, objectid, resourcetype):
        """
        get the key given an objectid
        """

        t = self.gethelper(objectid, resourcetype, None, True)

        if t is None:
            return None
        return t["prikey"]

    def getlength(self, objid, resourcetype):
        """
        returns the song length
        """

        t = self.gethelper(objid, resourcetype, None, False)

        if t is None:
            return None
        return t["length"]

    def getpublicurl(self, objid, resourcetype):
        """
        returns the public url
        """

        t = self.gethelper(objid, resourcetype, None, False)

        if t is None:
            return None
        return t["publicurl"]

    def getstreamingurl(self, objid, resourcetype):
        """
        returns the public streaming url
        """

        t = self.gethelper(objid, resourcetype, None, False)

        if t is None:
            return None
        return t["streamurl"]

    def getupdates(self):
        """
        returns a dict of changes {online, offline, uploaderr} as dicts

        FIXME: This can be error prone depending on the order of duplicate songids in the changes table
        """

        ret = {"online": [], "offline": [], "uploaderr": []}

        entries = self.db.table("changes").limit(100).run(self.conn)

        for e in entries:

            if e["status"] == 1:
                obj = {"id": e["songid"], "url": e["info"]}  # length??
                ret["online"].append(obj)
            elif e["status"] == 0:
                obj = {"id": e["songid"]}
                ret["offline"].append(obj)
            elif e["status"] == -1:
                obj = {"id": e["songid"], "msg": e["info"]}
                ret["uploaderr"].append(obj)

            # self.db.table('changes').get(e["songid"]).delete().run(self.conn)

        return ret

    def removeupdated(self, update):
        self.db.table("changes").get(update["id"]).delete().run(self.conn)

    def gethelper(self, objid, resourcetype, table=None, throwexception=True):
        """
        returns a python dict
        """
        if not table:
            table = resourcetype.table_main()

        t = self.db.table(table).get(objid).run(self.conn)

        if throwexception and t is None:
            raise Exception("Entry Not Found")
        return t

    def updatehelper(
        self, objid, resourcetype, objdict, table=None, throwexception=True
    ):
        """
        Wraps the the update db call
            updates an object in the db specified by objid and resourcetype
            updates values based on objdict, a dict of key vals
        """

        if not table:
            table = resourcetype.table_main()

        t = self.db.table(table).get(objid).update(objdict).run(self.conn)

        if throwexception and t is None:
            # TODO update this exception
            raise Exception("Entry Not Found")
        return t

    def inserthelper(
        self, objid, resourcetype, objdict, table=None, throwexception=True
    ):
        """
        The insert wrapper
        wraps rethinkdb's insert method

        returns False or throws an exception on errors
        returns True on success
        """

        print(self.db)

        objdict[resourcetype.primarykey()] = objid

        if not table:
            table = resourcetype.table_main()

        ret = self.db.table(table).insert(objdict).run(self.conn)

        try:
            if ret["inserted"] == 1:
                return True
        except KeyError:
            if throwexception:
                raise Exception("Insert Error")
            else:
                return False

        if throwexception:
            raise Exception("Unknown Exception")
        else:
            return False
