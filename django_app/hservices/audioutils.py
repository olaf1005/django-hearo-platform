import logging

import audiotools


class InvalidFormatException(Exception):
    # Simple exception for audioutils
    pass


def string_to_format(s):
    # generates the format for conversion
    s = s.lower().strip()
    if s == "aac":
        return audiotools.AACAudio
    elif s in ["master", "flac"]:
        return audiotools.FlacAudio
    elif s == "mp3":
        return audiotools.MP3Audio
    elif s == "wav":
        return audiotools.WaveAudio

    raise InvalidFormatException
