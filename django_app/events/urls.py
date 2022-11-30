from django.urls import path, include, re_path

from django.contrib import admin

from . import views as eventv


admin.autodiscover()


urlpatterns = [
    re_path(r"^$", eventv.eventpage),
    re_path(r"^update/$", eventv.update),
    re_path(r"^edit-event-ajax/$", eventv.edit_event_ajax),
]
