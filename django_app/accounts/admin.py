from django.contrib import admin
from accounts import models

# Disable delete site wide
admin.site.disable_action("delete_selected")


class ProfileAdmin(admin.ModelAdmin):
    date_hierarchy = "date_added"
    list_filter = (
        "deactivated",
        "signed_artist_agreement",
        "signed_new_tc_aggreement",
        "down_to_jam",
        "on_air",
        "fanmail_private",
        "downloads_private",
        "profile_private",
        "splash_featured",
    )
    search_fields = ("user__username", "user__email", "name", "keyword", "short_name")

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Profile, ProfileAdmin)


class PersonAdmin(admin.ModelAdmin):
    date_hierarchy = "last_login"
    list_filter = (
        "verified",
        "is_musician",
        "jam_now",
    )
    search_fields = ("user__username", "user__email")

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Person, PersonAdmin)


class OrganizationAdmin(admin.ModelAdmin):
    list_filter = (
        "is_band",
        "is_venue",
        "is_label",
        "is_artist",
        "is_fan",
    )
    search_fields = ("user__username", "user__email")

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Organization, OrganizationAdmin)


class WalletAdmin(admin.ModelAdmin):
    date_hierarchy = "date_added"
    readonly_fields = (
        "user",
        "openpgp_key",
        "hedera_account_id",
        "hedera_private_key",
        "hedera_public_key",
        "token_balance",
        "token_balance_last_update",
        "date_added",
    )

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Wallet, WalletAdmin)


class MusicianAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Musician, MusicianAdmin)


class BandAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Band, BandAdmin)


class VenueAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Venue, VenueAdmin)


class LabelAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Label, LabelAdmin)


class MembershipAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Membership, MembershipAdmin)


class InstrumentAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Instrument, InstrumentAdmin)


class GenreAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.Genre, GenreAdmin)
