from django.urls import path, include, re_path

from django.contrib import admin

from . import views as searchviews


admin.autodiscover()


urlpatterns = [
    re_path(r"get-invites", searchviews.query_inviteable),
    re_path(r"get-artists", searchviews.query_artists),
]
