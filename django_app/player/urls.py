from django.urls import path, include, re_path

from . import views as playerviews


urlpatterns = [
    re_path(r"^obj-info$", playerviews.obj_info),
    re_path(r"^add-play$", playerviews.add_play),
    re_path(r"^remove-play$", playerviews.remove_play),
    re_path(r"^load-plays$", playerviews.load_plays),
    re_path(r"^history$", playerviews.history),
    re_path(r"^radio-songs$", playerviews.radio_songs),
    re_path(r"^radio-info$", playerviews.radio_info),
    re_path(r"^load-cards$", playerviews.load_cards),
    re_path(r"^update-playqueue-indices", playerviews.update_playqueue_indices),
    re_path(r"^update-state$", playerviews.update_player_state),
    re_path(r"^init-socket$", playerviews.init_socket),
]
