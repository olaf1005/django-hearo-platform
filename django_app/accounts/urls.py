from django.urls import path, include, re_path

from . import views as ac_views


urlpatterns = [
    re_path(r"^(?:profile)?(?:/)?$", ac_views.my_account_profile),
    re_path(
        r"^account-profile-ajax/?$",
        ac_views.account_profile_ajax,
        name="accounts_account_profile_ajax",
    ),
    re_path(r"^pages/$", ac_views.my_account_pages),  # for people
    re_path(r"^get-membership/$", ac_views.get_membership_snippet),
    re_path(r"^delete-page-ajax/$", ac_views.delete_page_ajax),
    re_path(r"^join-page-ajax/$", ac_views.join_page_ajax),
    re_path(
        r"^create-page-ajax/$",
        ac_views.create_page_ajax,
        name="accounts_create_page_ajax",
    ),
    re_path(r"^make-admin-ajax/$", ac_views.make_admin_ajax),
    re_path(r"^send-request-ajax/$", ac_views.send_request_ajax),
    re_path(r"^update-membership-split-ajax/$", ac_views.update_membership_split_ajax),
    re_path(r"^delete-admin-ajax/$", ac_views.delete_admin_ajax),
    re_path(r"^delete-member-ajax/$", ac_views.delete_member_ajax),
    re_path(r"^banner-ajax/$", ac_views.my_account_banner_ajax),
    re_path(r"^get-banner-upload-data/$", ac_views.get_banner_upload_data),
    re_path(r"^get-banner-data/$", ac_views.get_banner_ajax),
    re_path(r"^location/$", ac_views.my_account_location),
    re_path(r"^location-ajax/$", ac_views.my_account_location_ajax),
    re_path(r"^private-location-ajax/$", ac_views.my_account_private_location_ajax),
    re_path(r"^music/$", ac_views.my_account_music),
    re_path(r"^visuals/$", ac_views.my_account_visuals),
    re_path(r"^wallet/$", ac_views.my_account_wallet),
    re_path(r"^albums/$", ac_views.my_account_music),
    re_path(r"^videos/upload-video-ajax", ac_views.upload_video_ajax),
    re_path(r"^videos/delete-video-ajax", ac_views.delete_video_ajax),
    re_path(r"^user-settings-ajax/$", ac_views.user_settings_ajax),
    re_path(r"^change-password-ajax/$", ac_views.change_password_ajax),
    re_path(r"^privacy/$", ac_views.user_settings),
    re_path(r"^songs/$", ac_views.my_account_music),
    re_path(r"^photos-ajax/$", ac_views.upload_photos_ajax),
    re_path(r"^delete-photo/$", ac_views.delete_photo),
    re_path(r"^accept-artist-agreement/$", ac_views.accept_agreement),
    re_path(r"^profile-info/$", ac_views.my_account_info),
    re_path(r"^legal/$", ac_views.my_account_legal),
    re_path(r"^send-jam/$", ac_views.send_jam),
    # Disabled for tune.fm
    # re_path(r'^downloads/$', ac_views.my_account_downloads),
    # re_path(r'^change-default-download/$', ac_views.change_default_download),
    # re_path(r'^payment/$', ac_views.my_account_payment,
    #     name='accounts_my_account_payment'),
    re_path(r"^fan-feed/$", ac_views.get_fan_feed),
    re_path(r"^index/$", ac_views.index, name="accounts_index"),
]
