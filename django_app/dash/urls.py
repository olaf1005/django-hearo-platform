from django.urls import path, include, re_path

from . import views as dashv


urlpatterns = [
    re_path(r"^songs/?$", dashv.songs),
    re_path(r"^newest_songs/?$", dashv.newest_songs),
    re_path(r"^newest_profiles/?$", dashv.newest_profiles),
    re_path(r"^players/?$", dashv.players),
]
