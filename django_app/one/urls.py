from django.urls import path, include, re_path

from . import views as oneviews


urlpatterns = [
    re_path(r"url-for", oneviews.path_from_filters),
    re_path(r"(?P<path>.*).json$", oneviews.content_listings),
    re_path(r"$", oneviews.index, name="hearo_one_index"),
]
