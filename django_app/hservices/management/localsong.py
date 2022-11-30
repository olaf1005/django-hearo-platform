# LocalSong
#
# Depends on ThriftShop
import os.path

from infrared import Context
from tartar import ThriftShop

from .localformats import LocalFormats


class LocalSong(object):
    def __init__(self, songid, context=None, version="master"):
        """
            Creates the LocalSong Object

            A LocalSong represents the file managment information surrounding a
            given song and version within a particular context
        """

        self.songid = songid

        self.context = context
        if self.context is None:
            self.context = Context()

        self.key = ThriftShop(self.context).getKey(self.songid, ThriftShop.Song)

        self.formats = LocalFormats(self.context)
        if self.version == self.formats.valid(version):
            raise Exception("Version %s is not valid" % version)

    def getSongId(self):
        """
            returns the songid of the song object
        """
        return self.songid

    def getKey(self):
        """
            returns the key (filename) of the song object
        """
        return self.key

    def getFullPath(self):
        """
        returns the full path of the song on disk
        """
        return (
            str(self.basepath)
            + self.getRelativePath()
            + self.getKey()
            + "_"
            + self.getSuffix()
            + self.getExtension()
        )

    def getRelativePath(self):
        """
            returns the relative path
        """
        return "/" + str(self.version) + "/"

    def getSuffix(self):
        """
            returns the suffix that precedes te extension
        """
        return self.formats.suffix(self.version)

    def getExtension(self):
        """
            returns the file extension for the song file
        """

        return self.formats.extension(self.version)

    def onDisk(self):
        """
            does this object have a file on the local disk
        """
        return os.path.isfile(self.fullpath())

    def toFormat(self, format):
        """"
            createsa new song object with the same conext and id,
            but a different format
        """

        return HearoSong(self.context, self.songid, format)
