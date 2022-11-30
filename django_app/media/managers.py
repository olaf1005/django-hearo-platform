from django.db import models


class AlbumQuerySet(models.QuerySet):
    def available(self):
        return self.filter(available=False)


class SongQuerySet(models.QuerySet):
    def available(self):
        return self.filter(processing=False, deleted=False, visible=True, online=True)
