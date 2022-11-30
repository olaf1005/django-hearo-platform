from infrared import Context, HearoCloudFiles
from managment import LocalFormats, LocalSong, Briefcase


class Management(object):
    """
        In memory management of song files
    """

    def __init__(self, context=None):
        self.context = context
        if context is None:
            self.context = Context()

        self.bc = Briefcase()

        self.fmts = LocalFormats(self.context)

    def getSong(self, songid, format="master"):
        """
            Factory method for localsong creation
        """

        if not (format == self.fmts.isvalid(format)):
            raise Exception("invalid format")

        return LocalSong(songid, context=self.context, format)

    def songCheckOut(self, song):
        """

        """

        self.bc.incPath(sng.getFullPath())

    def songCheckIn(self, song):
        """

        """

        self.bc.decPath(sng.getFullPath())

    def cf_download(self, servicename, localsong, checkout=False):
        """
            download a file to a storage service
        """

        cf = HearoCloudFiles(self.context)

        path = localsong.getFullPath()
        key = localsong.getKey()

        if checkout:
            self.songCheckOut(localsong)

        return cf.download(servicename, key, path)

    def cf_upload(self, servicename, localsong, checkin=False):
        """
            upload a file to a storage service
        """

        cf = HearoCloudFiles(self.context)

        path = localsong.getFullPath()
        key = localsong.getKey()

        if checkout:
            self.songCheckIn(localsong)

        return cf.upload(servicename, key, path)
