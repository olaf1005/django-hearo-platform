from infrared import HearoS3
from .callmemaybe import CallMeMaybe


class HarlemShake(CallMeMaybe):
    """
    A class that contains an script for registering
    songs into tartar
    from a local disk
    """

    def directmail(self, songid, resourcetype, path, containeralias=None, userid=None):
        """
        A helper method to upload songs directly into
        tartar for testing
        """

        hs3 = HearoS3(self.context)

        if containeralias is None:
            containeralias = "dripdrop"

        serv = self.context.getService("s3")

        ret = hs3.upload(containeralias, path)

        if userid is None:
            userid = "system"

        x = resourcetype.primarykey()

        self.register(songid, ret["key"], userid, resourcetype)

        return ret["key"]

    def isuploaded(self, songid, resourcetype, containeralias=None):
        """
        Has a song been uploaded?
        """

        hs3 = HearoS3(self.context)

        if containeralias is None:
            containeralias = "dripdrop"

        key = self.getkey(songid, resourcetype)

        # the song is either on S3, or
        # has is now ready on cloudfiles
        if hs3.exists(containeralias, key):
            return True
        else:
            self.isready(songid, resourcetype)
