from tartar import HarlemShake
from tartar import CallMeMaybe
import unittest

from infrared import Context

resourcetype = CallMeMaybe.Song


class TestHarlemShake(unittest.TestCase):
    resourcetype = CallMeMaybe.Song

    def setUp(self):
        # subclasses override this method (for testing and for not)
        self.h = HarlemShake(Context(test=True))

    def testUpload(self):

        key = self.h.directmail(
            "0", resourcetype, "tests/cheer_long.wav", containeralias="dripdrop"
        )

        # these two tests are testing the wrong table in the database :(
        self.assertEqual(self.h.getkey("0", resourcetype), key)

        self.assertTrue(self.h.isuploaded("0", resourcetype))
