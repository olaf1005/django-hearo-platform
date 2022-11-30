from django.urls import path, include, re_path

from django.contrib import admin

from . import views as feedv


admin.autodiscover()


urlpatterns = [
    re_path(r"^$", feedv.index),
    re_path(r"^review-ajax$", feedv.review_ajax),
    re_path(r"^update-ajax$", feedv.update_ajax),
    re_path(r"^fan-ajax$", feedv.fan_ajax),
]
