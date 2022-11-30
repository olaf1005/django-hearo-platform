#
# TODO: This crap needs to be redone
#
from tartar import ThriftShop
import unittest

from infrared import Context
from infrared import install_tartar


class TestThriftShopSong(unittest.TestCase):

    resourcetype = ThriftShop.Song

    def setUp(self):
        # subclasses override this method (for testing and for not)

        install_tartar.InstallTarTar(Context(test=True)).reinstall()

        self.ts = ThriftShop(Context(test=True))

        for i in ["1", "2", "5", "100"]:
            obj = {
                "filename": i,
                "streamurl": i + ".com",
                "puburl": i + ".org",
                "length": 100,
            }
            self.ts.inserthelper(i, self.resourcetype, obj, throwexception=True)

    def test_getkey(self):
        # '1' -> 'key1', etc.
        for i in ["1", "2", "5", "100"]:
            k = self.ts.getkey(i, self.resourcetype)
            self.assertEqual(k, i)

    def test_getpublicurl(self):
        for i in ["1", "2", "5", "100"]:
            url = self.ts.getpublicurl(i, self.resourcetype)
            self.assertEqual(url, i + ".org")

    def test_getgetstreamingurl(self):
        for i in ["1", "2", "5", "100"]:
            url = self.ts.getstreamingurl(i, self.resourcetype)
            self.assertEqual(url, i + ".com")

    # def test_gethelper_normal(self):
    # 	for i in ['1','2','5','100']:
    # 		x = self.ts.gethelper(i,self.resourcetype, table='songs')
    # 		length = x['length']
    # 		truelen = int('10'+i)
    # 		self.assertEqual(length, truelen)
    # 		art = x["artist"]
    # 		self.assertEqual(art,'band'+i)

    def test_gethelper_err(self):
        with self.assertRaises(Exception):
            an = self.ts.gethelper("0", self.resourcetype, throwexception=True)

        with self.assertRaises(Exception):
            an = self.ts.gethelper("1", self.resourcetype, table="nothingreal")
