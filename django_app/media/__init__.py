default_app_config = "media.apps.MediaConfig"


class DownloadType:
    # DOWNLOAD_TYPES
    NONE = "none"
    ALBUM = "album"
    FREE = "free"
    NORMAL = "normal"
    NAME_PRICE = "name_price"

    CHOICES = (
        ("none", "Stream Only"),
        ("album", "Album Only"),
        ("free", "Free Download"),
        ("normal", "Fixed Price"),
        ("name_price", "Name Your Price"),
    )


class DownloadFormat:
    MP3_320 = "mp3_320"
    MP3_V0 = "mp3_v0"
    MP3_V2 = "mp3_v2"
    # M4A = 'm4a'
    FLAC = "flac"
    # AAC = 'aac'
    # OGG = 'ogg'

    CHOICES = (
        ("mp3_320", "MP3 320"),
        ("mp3_v0", "MP3 245"),
        ("mp3_v2", "MP3 190"),
        # ('m4a', 'M4A'),
        ("flac", "FLAC"),
        # ('aac', 'AAC'),
        # ('ogg', 'OGG'),
    )


TARTAR_FORMATS = {
    "mp3_320": "MP3",
    "mp3_v0": "MP3",
    "mp3_v2": "MP3",
    "flac": "FLAC",
    "wav": "WAV",
}
