from django.urls import path, include, re_path

from django.contrib import admin

from . import views as actv


admin.autodiscover()


urlpatterns = [re_path(r"^$", actv.get)]
