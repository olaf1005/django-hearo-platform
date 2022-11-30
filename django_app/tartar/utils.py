# tartar/tartar.py
#
# utilities:
#
# SongStatus
# CMMStatus


class CMMResource(object):
    def schema(self):
        raise NotImplementedException

    def primarykey(self):
        raise NotImplementedException

    def table_process(self):
        raise NotImplementedException

    def table_main(self):
        raise NotImplementedException

    def keys_default(self):
        """
            returns a tuple of default keys
        """
        raise NotImplementedException

    def table_failed(self):
        raise NotImplementedException

    def table_process(self):
        raise NotImplementedException

    def keys_final(self):
        """
            returns a tuple of reserved keys
        """
        return (
            "puburl",
            "privid",
            "streamurl",
        )


class CMMSong(CMMResource):
    """
        A class representing the Song File upload resource
    """

    def schema(self):
        """
            Song does not need to add anything special to the schema
        """
        return {}

    def primarykey(self):
        """
            Song's primary key is 'songid'
        """
        return "songid"

    def table_process(self):
        """
            song processing table
        """
        return "process"

    def table_main(self):
        """
            song storage table
        """
        return "songs"

    def table_failed(self):
        """

        """
        return "failures"

    def keys_default(self):
        """
            returns a tuple of default keys
        """
        return ("artist", "year", "songname", "albumname", "length")

    def keys_final(self):
        """
            returns a tuple of reserved keys, cannot be edited once created!
        """
        return (
            "songid",
            "puburl",
            "privid",
            "streamurl",
            "length",
        )


class CMMImage(CMMResource):
    """
        A class representing the Image File upload resource
    """

    def __init__(self):
        """
            sets the initial value of type
        """
        self.type = "unknown"

    def schema(self):
        """
            schema additions
        """
        return {"target": self.type}

    def primarykey(self):

        return "imgid"

    def table_process(self):
        """
            image processing table
        """
        return "imgproc"

    def table_main(self):
        """
            image main storage table
        """
        return "imgtab"

    def keys_default(self):
        """
            returns a tuple of default keys
        """
        return ("width", "height", "format")

    def keys_final(self):
        """
            returns a tuple of reserved keys
        """
        return ("imgid", "puburl", "privid", "streamurl")

    def settype(self, type):
        """
            set the type target of an Image Resource
        """
        self.type = type


class CMMImg:
    profile = CMMImage().settype("profile")
    album = CMMImage().settype("album")
    banner = CMMImage().settype("banner")
    unknown = CMMImage()
