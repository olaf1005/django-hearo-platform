#
# maintains routing for backend services
#
#
import json
import uuid
import random

from rethinkdb import r


PATH_TEST = "tests/test.config"


class Context(object):
    "Represents the environment for which this part of hearo is operating"

    def __init__(self, configpath, test=False):
        """Note: Do not call rethinkdb unless it is needed """

        if test:
            configpath = PATH_TEST

        fil = open(configpath, "r")
        self.context = json.load(fil)
        self.db = None
        self.pathappend = ""

    def setPath(self, s):
        """ Narrow the path to another environment """
        self.pathappend = s + "/"

    def getBasePath(self):
        """ returns the basepath for local file storage """
        return self.context["basepath"] + self.pathappend

    def getDB(self):
        """ connects to our DB

            will have latency down the road considered to be a private method
        """

        if self.db is not None:
            return (self.db, self.conn)

        x = self.getService("rethink")

        dbname = x["name"]

        host = random.choice(x["nodelist"])

        self.conn = r.connect(host=host, port=28015).repl()
        self.db = r.db(dbname)

        return (self.db, self.conn)

    def getService(self, servicename):
        """ returns a python dict representing the service """

        for service in self.context["services"]:
            if service["service"] == servicename:
                return service
        return None

    def getUUID(self, suffix=None, prefix=True):
        """ utiltiy method for generating uuids """

        if suffix is None:
            suffix = ""

        if prefix:
            return "{}_{}{}".format(
                self.context["version_prefix"],
                str(uuid.uuid4()).replace("-", ""),
                suffix,
            )
        else:
            return "{}{}".format(str(uuid.uuid4()).replace("-", ""), suffix)

    def getContext(self):
        """ get the context """
        return self.context
