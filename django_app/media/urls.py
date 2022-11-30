from django.urls import path, include, re_path

from . import views as mediav


urlpatterns = [
    re_path(
        r"^song-details/$", mediav.edit_music_entity_details, {"entity_type": "song"}
    ),
    re_path(r"^delete-song/$", mediav.delete_song_ajax),
    re_path(r"^create-album/$", mediav.create_album),
    re_path(
        r"^album-details/$", mediav.edit_music_entity_details, {"entity_type": "album"}
    ),
    re_path(r"^upload-album-cover/$", mediav.album_cover_ajax),
    re_path(r"^delete-album/$", mediav.delete_album_ajax),
    re_path(r"^filetype-error/$", mediav.log_compressed_clientside_error),
]
