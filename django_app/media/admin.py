from django.contrib import admin
from media import models


class ListenAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Listen, ListenAdmin)


class VideoAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Video, VideoAdmin)


class PhotoAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Photo, PhotoAdmin)

# admin.site.register(models.Banner)
# admin.site.register(models.Radio)


class MusicUploadAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.MusicUpload, MusicUploadAdmin)


class AlbumAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Album, AlbumAdmin)


class SongAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Song, SongAdmin)
