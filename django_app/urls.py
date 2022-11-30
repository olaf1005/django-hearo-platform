from django.urls import path, include, re_path
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib import admin
from django.views.static import serve

import common.errors
import one.views
import utils
import accounts.views
import accounts.chill
import gangnam_client
import events.views
import feeds.views
import media.views
import support.views

from django.conf import settings

handler404 = common.errors.handler404
handler500 = common.errors.handler500


urlpatterns = [
    # Static files
    re_path(r"^public/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    re_path(
        r"^cache/(?P<path>.*)$", serve, {"document_root": settings.IMAGE_CACHE_DIR}
    ),
    re_path(r"^images/(?P<path>.*)$", serve, {"document_root": settings.IMAGES_DIR}),
    # Account management
    re_path(r"^my-account/", include("accounts.urls")),
    re_path(r"^my-media/", include("media.urls")),
    # Info
    re_path(r"^api/v0/", include("apiv0.urls")),
    # re_path(r'^shows/', include('events.urls')),
    re_path(r"^mail/", include("mail.urls")),
    re_path(r"^dash/", include("dash.urls")),
    re_path(r"^player/", include("player.urls")),
    # Disabled for tune.fm
    # re_path(r'^payment/', include('payment_processing.urls')),
    re_path(r"^search/", include("search.urls")),
    re_path(r"^haystack/", include("haystack.urls")),
    re_path(r"^directory/", one.views.redirect_to_map),
    # Utils
    re_path(r"^get-autocomplete/", utils.get_autocomplete),
    re_path(r"^ping/$", accounts.views.ping),
    re_path(r"^download/(?P<packageid>.*)$", gangnam_client.download_page),
    re_path(r"feeds/", include("activity.urls")),
    re_path(r"music/fan-ajax/", feeds.views.fan_ajax),
    re_path(r"^refresh-header/$", accounts.views.refresh_header),
    # google webmaster tools
    re_path(
        r"^googlefae7e26d85280941\.html$",
        lambda r: HttpResponse(
            "google-site-verification: googlefae7e26d85280941.html",
            content_type="text/plain",
        ),
    ),
    re_path(r"not-verified/$", accounts.views.not_verified, name="not_verified"),
    # robots.txt
    re_path(
        r"^robots\.txt$",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
    # about page
    re_path(r"^about/$", accounts.views.about, name="about"),
    # Social join
    re_path(r"^join/social/$", accounts.views.join_social, name="join_social"),
    re_path(r"^join/welcome/$", accounts.views.join_welcome, name="join_welcome"),
    re_path(r"^join/$", accounts.views.join_index, name="join_index"),
    # Landing
    re_path(r"^signup/$", accounts.views.signup, name="signup"),
    # Login/logout
    re_path(r"^login/$", accounts.views.login_ajax, name="login"),
    re_path(r"^logout/$", accounts.views.log_out, name="logout"),
    # Statuses
    re_path(r"^delete-post-ajax", accounts.views.delete_post_ajax),
    re_path(r"^post-status/$", accounts.views.post_status_ajax),
    # Reviews
    re_path(r"^post-review/$", accounts.views.post_review_ajax),
    re_path(r"^get-reviews/$", accounts.views.get_reviews),
    re_path(
        r"^reviews/artwork/(?P<elem_type>\w*)/(?P<elem_id>\w*)$",
        accounts.views.review_artwork,
    ),
    # Photos
    re_path(r"^get-primary-photo/", accounts.views.get_primary_photo),
    # Profile
    re_path(r"^deactivate-account/$", accounts.views.deactivate_account),
    re_path(
        r"^register-ajax/$", accounts.views.register_ajax, name="accounts_register_ajax"
    ),
    re_path(r"^check-register-ajax/$", accounts.views.check_register_ajax),
    re_path(r"^ajax/build/song_listings/", accounts.views.group_of_song_listings),
    re_path(r"^switch-account/", accounts.views.switch_account),
    re_path(r"^privacy-policy/", accounts.views.privacy_policy, name="privacy_policy"),
    re_path(r"^terms/", accounts.views.terms_of_use, name="terms"),
    re_path(r"^copyright/", accounts.views.copyright_agreement),
    re_path(r"^artist-agreement/", accounts.views.artist_agreement),
    re_path(r"^get-profile-progress-ajax/", accounts.views.get_profile_progress_ajax),
    re_path(r"^check-register-email/", accounts.views.check_register_email),
    re_path(r"^crop-photo/$", accounts.views.crop_photo),
    re_path(r"^get-photo-details/$", accounts.views.get_photo_details),
    re_path(r"^set-profile-pic/$", accounts.views.set_profile_pic),
    re_path(r"^upload-banner-temp/$", accounts.views.upload_banner_temp),
    re_path(r"^fandlib-ajax/$", accounts.views.fandlib_ajax),
    re_path(r"^new-banner-submit/$", accounts.views.new_banner_submit),
    re_path(
        r"^delete-temp-banner-texture/$", accounts.views.delete_temp_banner_texture
    ),
    re_path(r"^crop-banner/$", accounts.views.crop_banner),
    re_path(r"^get-profile-events/$", accounts.views.get_profile_events_ajax),
    re_path(r"^delete-event-ajax/$", accounts.views.delete_event_ajax),
    # Send email
    re_path(r"^send-feedback/$", accounts.views.send_feedback),
    re_path(r"^send-invites/$", accounts.views.send_invites),
    # Profile module adjustments
    re_path(
        r"^profile-layout-setting/?$", accounts.views.adjust_profile_layout_setting
    ),
    # Email stuff
    re_path(r"^password-recovery/$", accounts.views.password_recovery),
    re_path(r"^send-recovery/$", accounts.views.send_recovery),
    re_path(r"^verify/$", accounts.views.verify),
    re_path(r"^send-verification/$", accounts.views.send_verification),
    re_path(r"^chill-plugin-ajax/$", accounts.chill.query),
    # Events
    re_path(r"^get-event/$", events.views.get_event),
    # Media
    re_path(r"^song-listen/$", media.views.song_listen),
    re_path(r"^get-download-status/$", media.views.get_download_status),
    re_path(r"^cmm-register/$", media.views.cmm_register),
    re_path(r"^get-signature/$", media.views.get_signature),
    re_path(r"^reorder-songs/$", media.views.reorder_songs_ajax),
    re_path(r"^delete-song-ajax/$", media.views.delete_song_ajax),
    re_path(r"^failed-upload/$", media.views.real_delete),
    re_path(r"^get-album-songs/$", media.views.get_album_songs),
    re_path(r"^save-album-songs/$", media.views.save_album_songs),
    re_path(r"^get-album/$", media.views.get_album),
    re_path(r"^album-info/$", media.views.album_info),
    re_path(r"^song-cover/(\d+)/$", media.views.song_cover),
    # Temp hack (Needs to be at the bottom?)
    re_path(r"^song/(?P<slug>[-\w]+)$", media.views.song_view),
    # re_path(r'^album/(?P<slug>[-\w]+)$', media.views.album_view),
    re_path(r"^profile/(?P<slug>[-\w]+)/info/?$", accounts.views.profile_info_ajax),
    re_path(
        r"^profile/(?P<slug>[-\w]+)/?(?P<section>[\w]+)?/?.*$", accounts.views.profile,
    ),
    path("newsletter/", include("newsletter.urls")),
    # Admin
    path(
        "support/download_openpgp_private_key/",
        support.views.download_openpgp_private_key,
    ),
    path(
        "admin/support/download_openpgp_public_key/",
        support.views.download_openpgp_public_key,
    ),
    path(
        "admin/support/regenerate_encryption_keys/",
        support.views.regenerate_encryption_keys,
    ),
    path("admin/export_user_emails/", accounts.views.export_user_emails),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    # Needs to be last pattern
    re_path(r"", include("one.urls")),
]
