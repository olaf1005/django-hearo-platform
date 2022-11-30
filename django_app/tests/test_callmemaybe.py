from callmemaybe import CallMeMaybe
import unittest

resourcetype = CallMeMaybe.Song


class TestCallMeMaybe(unittest.TestCase):
    resourcetype = CallMeMaybe.Song

    def setUp(self):
        # subclasses override this method (for testing and for not)
        self.cmm = CallMeMaybe("tests/filldb.json")

    def test_register(self):
        """
		register(objid, filename, userid, resourcetype)
		TODO: rewrite register to be testable
		"""
        pass

    def test_isready(self):
        for objid in ["1", "2", "5", "100"]:
            ready = self.cmm.isready(objid, self.resourcetype)
            self.assertTrue(ready)

    def test_isntready(self):
        for objid in ["200", "asdf", "45"]:
            self.assertFalse(self.cmm.isready(objid, self.resourcetype))

    def test_hasfailed(self):
        pass

    def test_whatstage(self):
        pass

    def test_setmeta_false(self):
        m = self.cmm.setmeta("1", resourcetype, {})
        self.assertFalse(m)

        m = self.cmm.setmeta("1", resourcetype, None)
        self.assertFalse(m)

    def test_setting_final(self):
        newm = {"length": "10000000"}
        b = self.cmm.setmeta("1", resourcetype, newm)
        old = {"length": 101}
        new = self.cmm.getmeta("1", resourcetype, ("length",))
        self.assertEqual(old, new)

    def test_meta(self):
        for i in ["1", "2", "5"]:
            m = self.cmm.getmeta(i, resourcetype)

            # ('artist', 'year', 'songname', 'albumname', 'length')
            should = {
                "artist": "band" + i,
                "year": int("200" + i),
                "songname": "song" + i,
                "albumname": "album" + i,
                "length": int("10" + i),
            }
            self.assertEqual(m, should)
        new = {"artist": "Charlie Harrison", "songname": "My Song"}
        m = self.cmm.setmeta("2", resourcetype, new)
        self.assertTrue(m)

        self.assertEqual(
            self.cmm.getmeta("2", resourcetype, ("artist", "songname")), new
        )
