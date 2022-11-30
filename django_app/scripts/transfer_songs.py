"""
Transfers files from localhost to cloud
"""
import django

django.setup()

from django.conf import settings

from media.models import Song

from tartar import HarlemShake
from infrared import Context


def iterate():
    songs = Song.objects.filter(deleted=False)
    shake = HarlemShake(Context(settings.CONFIG))
    for s in songs:
        info = (s.id, HarlemShake.Song, s.file.path, s.profile.id)
        print(info)
        shake.directmail(*info)


if __name__ == "__main__":
    iterate()
