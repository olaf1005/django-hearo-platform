from django.urls import path, include, re_path

from django.contrib import admin

from . import views as payviews


admin.autodiscover()


urlpatterns = [
    re_path(r"^(?:card_info)?(?:/)?$", payviews.card_info),
    re_path(r"^(?:add_card)?(?:/)?$", payviews.add_card),
    re_path(r"^(?:remove_card)?(?:/)?$", payviews.remove_card),
    re_path(r"^(?:buy_songs)?(?:/)?$", payviews.buy_download_queue),
    re_path(r"^(?:update_bank_info)?(?:/)?$", payviews.set_bank_info),
    # re_path(r'^(?:create_ach)?(?:/)?$', payviews.create_ach),
    re_path(r"^(?:cash_out)?(?:/)?$", payviews.cash_out),
]
