from django.urls import path, include, re_path

from . import music, queues, my


urlpatterns = [
    # Music
    re_path(r"^song~(?P<songid>\d+)$", music.song),
    re_path(r"^album~(?P<albumid>\d+)$", music.album),
    re_path(r"^profile~(?P<profileid>\d+)$", music.profile),
    re_path(r"^my/cards$", my.cards),
    # Download and Playlist queues
    re_path(
        r"^queues/downloads/album~(?P<item_id>\d+)$",
        queues.downloads_DELETE,
        {"item_type": "album"},
    ),
    re_path(
        r"^queues/downloads/song~(?P<item_id>\d+)$",
        queues.downloads_DELETE,
        {"item_type": "song"},
    ),
    re_path(
        r"^queues/downloads/profile~(?P<item_id>\d+)$",
        queues.downloads_DELETE,
        {"item_type": "profile"},
    ),
    re_path(r"^queues/downloads$", queues.downloads),
    re_path(r"^queues/playlist~(?P<song_id>\d+)$", queues.playlist_DELETE),
    re_path(r"^queues/playlist$", queues.playlist),
    # re_path(r'^queues/downloads/(?P<entity_type\w+)~?(?P<entity_id>\d+)?$',
    # 'modify_downloads'),
    # re_path(r'^queues/playlist/(?P<entity_type\w+)~?(?P<entity_id>\d+)?$',
    # 'modify_playlist'),
]
