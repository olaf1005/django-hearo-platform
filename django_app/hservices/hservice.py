# hservice
#
# HearoService is the baseclass for Hearo's backend python daemon services
#
# v0.1

import datetime
import time
import logging

from infrared import Context


logger = logging.getLogger("tartar.hservices.hservice")


class HearoService(object):
    def __init__(self, servicename, context=None):
        """
            initializes a HearoService
        """

        self.name = servicename

        # self.management = Managment(self.context)

        self.context = context

        if not self.context:
            self.context = Context()

        (self.db, self.conn) = self.context.getDB()

        logger.info("db: %s", self.db)

        # checkin
        future = datetime.datetime.now() + datetime.timedelta(minutes=5)
        self.checkin = time.mktime(future.timetuple())
        # origin
        self.birth = self.checkin

        ret = (
            self.db.table("services")
            .insert({"name": self.name, "birth": self.birth, "checkin": self.checkin,})
            .run(self.conn)
        )

        # gets uuid
        self.uuid = ret["generated_keys"][0]
        logger.info("uuid is: %s", self.uuid)

    def hello(self):
        """
        checkins in to the database
        """
        # future = datetime.datetime.now() + datetime.timedelta(minutes=5)
        # future.timetuple()
        self.checkin = time.mktime(datetime.datetime.now().timetuple())
        self.db.table("services").get(self.uuid).update({"checkin": self.checkin}).run(
            self.conn
        )
