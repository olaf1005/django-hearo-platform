#
# A very, very basic test for hearocloudfiles
#
#

import logging
import unittest

from infrared.hearocloudfiles import *
from infrared.hearos3 import *
from infrared.context import Context


logger = logging.getLogger(__name__)


class TestHearoStorage(unittest.TestCase):
    def setUp(self):
        self.cf = HearoCloudFiles(Context(test=True))
        self.cf.delete("test", "testkey")

        self.s3 = HearoS3(Context(test=True))
        self.s3.delete("test", "testkey")

    def testUploads(self):

        for x in [self.cf, self.s3]:

            self.assertFalse(x.exists("test", "testkey"))
            x.reUpload("test", "testkey", "tests/test.config")
            self.assertTrue(x.exists("test", "testkey"))
            x.reUpload("test", "testkey", "tests/test.cfobject")
            self.assertTrue(x.exists("test", "testkey"))

            x.download("test", "testkey", "tests/test_.cfobject")
            self.assertTrue(x.exists("test", "testkey"))

            x.delete("test", "testkey")
            self.assertFalse(x.exists("test", "testkey"))
