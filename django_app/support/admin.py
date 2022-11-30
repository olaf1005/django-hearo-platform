import itertools
import pgpy

from django.contrib import admin
from django.contrib.auth.models import UserManager
from django import forms
from django.core.exceptions import SuspiciousOperation
from django.conf import settings

from accounts.models import WalletRecovery

import openpgp_utils
import utils

from . import models, PasswordResetRequestStatus


class PasswordResetAuthorizerForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = models.PasswordResetRequestAuthorizer
        fields = ["authorizer", "pgp_file", "password"]


class PasswordResetAuthorizerInline(admin.TabularInline):
    model = models.PasswordResetRequestAuthorizer
    max_num = settings.NUM_AUTHORIZERS_REQUIRED_FOR_PASSWORD_RESET + 1
    extra = 1
    form = PasswordResetAuthorizerForm

    def has_change_permission(self, request, obj=None):
        return False


class PasswordResetRequestAdmin(admin.ModelAdmin):
    class Media:
        # Disable add another user button
        css = {"all": ("css/no-addanother-button.css",)}

    inlines = (PasswordResetAuthorizerInline,)
    date_hierarchy = "date"
    list_display = ("user", "date", "status", "assigned_to")
    list_display_links = ("user",)
    fieldsets = (
        (None, {"fields": (("user", "date",), ("assigned_to",))}),
        ("KYC", {"fields": (("kyc_image", "kyc_date"), ("kyc_image_2", "kyc_date_2"))}),
        ("Details", {"fields": (("status",), ("reason", "partial_key"))}),
    )
    list_filter = ("status", "assigned_to")
    list_editable = ("assigned_to",)
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ["user"]
    exclude = ["added_by", "date_added"]

    def get_actions(self, request):
        # Disable delete if not already disabled site wide
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_readonly_fields(self, request, obj=None):
        # Disable editing usere field if request was denied or password reset
        readonly_fields = ("kyc_date", "kyc_date_2", "partial_key")
        if obj is not None and obj.status in ["request denied", "password reset"]:
            return readonly_fields + ("user",)
        return readonly_fields

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in ["request denied", "password reset"]:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Only set added_by during the first save.
            obj.added_by = request.user

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        has_deleted_objects = False
        for obj in formset.deleted_objects:
            # if an object is deleted, we have to reset the unlock process
            # since we no longer have a record of who authoorized the unlock
            # hence we reattempt using just the provided keys
            has_deleted_objects = True
            obj.delete()

        if has_deleted_objects:
            form.instance.partial_key = None
            form.instance.save()

        keys = []
        for instance in instances:
            # if fields are set proceed to add it to to list of keys used to
            # decrypt, if the file and password are not set, that means
            # they were already used in the unlock attempt so we have a
            # partial key
            instance.added_by = request.user
            if instance.password:
                priv_key = None
                email = None
                password = instance.password
                instance.password = "*********"
                if instance.pgp_file:
                    # we replace the data here so that it cant be read
                    # but we still want to keep a reference to the filename
                    # (this can of course be faked but less likely)
                    key = instance.pgp_file.read()
                    instance.pgp_file.truncate()
                    priv_key = pgpy.PGPKey()
                    priv_key.parse(key)
                elif instance.authorizer:
                    # If the key wasn't specified, fetch the key object
                    priv_key = instance.authorizer.wallet.get_openpgp_key_object()
                    email = instance.authorizer.email
                instance.save()
                keys.append(
                    {"email": email, "priv_key": priv_key, "password": password}
                )

        # track key decryption
        decrypted_key = None

        # if we have met the threshold
        # check if we can decrypt the user keys with the keys provided
        if (
            form.instance.passwordresetrequestauthorizer_set.count()
            >= settings.NUM_AUTHORIZERS_REQUIRED_FOR_PASSWORD_RESET
        ):
            # then attempt decryption and send the user an email
            # if successful
            if form.instance.partial_key:
                # if we have a partial key, use the additional keys to attempt
                # decryption, if we succeed, continue

                message = form.instance.partial_key
                for key in keys:
                    message = pgpy.PGPMessage.from_blob(message)
                    with key["priv_key"].unlock(key["password"]) as unlocked_key:
                        message = unlocked_key.decrypt(message).message
                        if len(message) == 96:
                            # We have the key
                            decrypted_key = message
                            break
            else:
                # handle case when we input the required auathorizations at form create
                # (when no partial key is set)
                for key in keys:
                    if not key["priv_key"] or not key["password"]:
                        break
                    with key["priv_key"].unlock(key["password"]) as unlocked_key:
                        for recoverywallet in WalletRecovery.objects.filter(
                            wallet=form.instance.user.wallet
                        ):
                            try:
                                decrypted_message = unlocked_key.decrypt(
                                    recoverywallet.get_encrypted_key_object()
                                )
                            except (
                                pgpy.errors.PGPDecryptionError,
                                pgpy.errors.PGPError,
                            ):
                                pass
                            else:
                                # we have a decrypted message
                                break

                message = decrypted_message.message
                for key in keys:
                    message = pgpy.PGPMessage.from_blob(message)
                    with key["priv_key"].unlock(key["password"]) as unlocked_key:
                        message = unlocked_key.decrypt(message).message
                        if len(message) == 96:
                            # We have the key
                            decrypted_key = message
                            break
        else:
            # if we haven't met the threshold, we attempt decryption and store the partial key
            # we can do this quickly without having to lookup walletrecovery objects since
            # we have a reference to the wallet recovery objects that can be decrypted
            decrypted_message = None

            if keys:
                if form.instance.partial_key:
                    # attempt with partial key
                    message = form.instance.partial_key
                    for key in keys:
                        if not key["priv_key"] or not key["password"]:
                            break
                        message = pgpy.PGPMessage.from_blob(message)
                        with key["priv_key"].unlock(key["password"]) as unlocked_key:
                            try:
                                message = unlocked_key.decrypt(message).message
                            except (
                                pgpy.errors.PGPDecryptionError,
                                pgpy.errors.PGPError,
                            ):
                                pass
                            else:
                                # we have a decrypted message
                                decrypted_message = message
                else:
                    # if we don't have a partial key, we need to get one
                    for key in keys:
                        if not key["priv_key"] or not key["password"]:
                            break
                        with key["priv_key"].unlock(key["password"]) as unlocked_key:
                            for recoverywallet in WalletRecovery.objects.filter(
                                wallet=form.instance.user.wallet
                            ):
                                try:
                                    decrypted_message = unlocked_key.decrypt(
                                        recoverywallet.get_encrypted_key_object()
                                    ).message
                                except (
                                    pgpy.errors.PGPDecryptionError,
                                    pgpy.errors.PGPError,
                                ):
                                    pass
                                else:
                                    # we have a decrypted message
                                    break
                if decrypted_message is None:
                    raise SuspiciousOperation(
                        "Either the key supplied or unlock password was incorrect"
                    )

                # form.instance.partial_key = decrypted_message.message
                form.instance.partial_key = decrypted_message
                form.instance.save()

        if decrypted_key:
            # if we managed to decrypt the key at this stage, we
            # - reencrypt key using a new pasasword
            # - reset partial key
            # - update the status of the instance to
            # - remove
            #
            form.instance.status = PasswordResetRequestStatus.PASSWORD_RESET
            form.instance.partial_key = None
            form.instance.save()

            user = form.instance.user
            email = form.instance.user.email
            new_password = UserManager().make_random_password()
            wallet = form.instance.user.wallet
            full_name = "{} {}".format(user.first_name, user.last_name)
            key = openpgp_utils.create_key(full_name, email)
            openpgp_utils.lock(key, new_password)

            # reencrypt the hedera private key
            # Create message and encrypt
            message = pgpy.PGPMessage.new(decrypted_key)
            encrypted_private_key = str(key.pubkey.encrypt(message))
            wallet.openpgp_key = str(key)
            wallet.hedera_private_key = encrypted_private_key
            wallet.save()

            utils.sendemail_template(
                [form.instance.user.email],
                "email_notifications/send_account_unlocked_email.html",
                {"user": user, "new_password": new_password},
            )

            user.set_password(new_password)
            user.person.should_change_pass = True
            user.person.save()
            user.save()
        else:
            # full decryption was not possible, so do nothing
            # since the instance will be upto date
            pass

        formset.save_m2m()


admin.site.register(models.PasswordResetRequest, PasswordResetRequestAdmin)


class GeneralRequestAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    list_display = (
        "user",
        "date",
        "status",
    )
    list_display_links = ("user",)
    fieldsets = (
        (None, {"fields": (("date",), ("user",), ("assigned_to",))}),
        ("KYC", {"fields": (("kyc_image", "kyc_date"),)}),
        ("Details", {"fields": (("status",), ("request"))}),
    )
    list_filter = ("status",)
    list_editable = ("status",)
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ["user"]

    def get_actions(self, request):
        # Disable delete if not already disabled site wide
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ("date", "kyc_date", "kyc_date_2")
        # Disable editing usere field if request was denied or password reset
        if obj is not None:
            return readonly_fields + ("user",)
        return readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        # Disable add another user button
        css = {"all": ("css/no-addanother-button.css",)}


admin.site.register(models.GeneralRequest, GeneralRequestAdmin)
