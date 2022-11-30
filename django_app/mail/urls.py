from django.urls import path, include, re_path

from django.contrib import admin

from . import views as mailv


admin.autodiscover()


urlpatterns = [
    re_path(r"^$", mailv.index),
    re_path(r"^inbox/?$", mailv.inbox),
    re_path(r"^send-message/?$", mailv.send_message),
    re_path(r"^view/?$", mailv.view),
    re_path(r"^delete/?$", mailv.delete),
    re_path(r"^mark-read/?$", mailv.mark_read),
    re_path(r"^check-for-new/?$", mailv.check_for_new),
    re_path(r"^unread-count/?$", mailv.update_unread),
]
