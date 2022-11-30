"""Requests to reset passwords while keeping keys (Hence JAM) are made using
this app
"""

import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

import utils

from . import PasswordResetRequestStatus, GeneralRequestStatus, GeneralRequestType


class PasswordResetRequest(models.Model):
    date_added = models.DateTimeField(auto_now_add=True)
    date = models.DateField(default=datetime.date.today)
    user = models.ForeignKey(
        User,
        related_name="password_reset_support_requests",
        on_delete=models.CASCADE,
        help_text="The user making the request",
    )
    kyc_image = models.ImageField(
        upload_to="images/kyc",
        null=True,
        blank=True,
        help_text="Enter a KYC image",
        verbose_name="KYC image",
    )
    kyc_image_2 = models.ImageField(
        upload_to="images/kyc_2",
        null=True,
        blank=True,
        help_text="Enter a second KYC image if required",
        verbose_name="KYC image 2",
    )
    kyc_date = models.DateTimeField(null=True, blank=True, verbose_name="Date")
    kyc_date_2 = models.DateTimeField(null=True, blank=True, verbose_name="Date")
    status = models.CharField(
        default="unverified", choices=PasswordResetRequestStatus.CHOICES, max_length=50
    )
    reason = models.TextField(
        null=False,
        blank=False,
        help_text="Enter a reason for the request, e.g. user forgot password",
    )
    added_by = models.ForeignKey(
        User,
        limit_choices_to={"is_staff": True},
        related_name="added_password_reset_requests",
        on_delete=models.CASCADE,
        help_text="Staff member who initiated the request",
    )
    # The workflow for authorization requires that admin user a first authorizes with a key, then admin user b
    # a partial key is generated when admin user a authorizes
    partial_key = models.TextField(
        null=True,
        blank=True,
        help_text="This is the partial key which will be removed once decrypted and sent to the user",
    )
    # Who is the next person who should authorize the request
    assigned_to = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name="assigned_password_reset_requests",
        limit_choices_to={"is_staff": True},
        help_text="Assign next step of request to a user and send them an email",
    )

    def __str__(self):
        return "{} - {} - {}".format(self.date, self.status, self.user)

    class Meta:
        ordering = ("date",)
        verbose_name_plural = "password reset requests"

    def save(self, *args, **kwargs):
        if self.kyc_image and not self.kyc_date:
            self.kyc_date = timezone.now()
        if self.kyc_image_2 and not self.kyc_date_2:
            self.kyc_date_2 = timezone.now()
        if (
            self.assigned_to
            and not self.status == PasswordResetRequestStatus.PASSWORD_RESET
        ):
            utils.sendemail(
                "Password reset request assigned",
                self.assigned_to.email,
                "A password reset request has been assigned to you: https://tune.fm/admin/support/passwordresetequest/{}".format(
                    self.pk
                ),
            )
        super().save(*args, **kwargs)


class PasswordResetRequestAuthorizer(models.Model):
    password_reset_request = models.ForeignKey(
        PasswordResetRequest, on_delete=models.CASCADE
    )
    date = models.DateTimeField(auto_now_add=True, help_text="Auto")
    authorizer = models.ForeignKey(
        User,
        related_name="authorized_requests",
        null=True,
        blank=True,
        limit_choices_to={"is_staff": True},
        on_delete=models.CASCADE,
        help_text="The user authorizing the request",
    )
    added_by = models.ForeignKey(
        User,
        related_name="added_authorized_requests",
        limit_choices_to={"is_staff": True},
        on_delete=models.CASCADE,
        help_text="The user who added the auathorization",
    )
    # The contents of these fields are never stored and are only ever used
    # to unlock a partial key
    password = models.CharField(null=True, blank=True, default=None, max_length=100)
    pgp_file = models.FileField(null=True, blank=True, default=None)

    class Meta:
        ordering = ("date",)
        verbose_name_plural = "authorizers"

    def __str__(self):
        return str(self.date)


class GeneralRequest(models.Model):
    date = models.DateTimeField(auto_now_add=True, help_text="Auto")
    user = models.ForeignKey(
        User,
        related_name="general_support_requests",
        on_delete=models.CASCADE,
        help_text="The user making the request",
    )
    kyc_image = models.ImageField(
        upload_to="images/kyc",
        null=True,
        blank=True,
        help_text="Enter a KYC image if required",
    )
    kyc_date = models.DateTimeField(
        null=True, blank=True, help_text="This field is auto populated"
    )
    status = models.CharField(
        default="unverified", choices=GeneralRequestStatus.CHOICES, max_length=50
    )
    type = models.CharField(
        default="unverified", choices=GeneralRequestType.CHOICES, max_length=50
    )
    request = models.TextField(
        null=False,
        blank=False,
        help_text="Enter a the request, e.g. user cant upload a song",
    )
    assigned_to = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name="assigned_general_requests",
        limit_choices_to={"is_staff": True},
        help_text="Assign next step of request to a user and send them an email",
    )

    def __str__(self):
        return "{} - {} - {}".format(self.date, self.status, self.user)

    class Meta:
        ordering = ("date",)
        verbose_name_plural = "general requests"

    def save(self, *args, **kwargs):
        if self.kyc_image and not self.kyc_date:
            self.kyc_date = timezone.now()
        if self.assigned_to:
            utils.sendemail(
                "Password reset request assigned",
                self.assigned_to.email,
                "A password reset request has been assigned to you: https://tune.fm/admin/support/passwordresetequest/{}".format(
                    self.pk
                ),
            )
        super().save(*args, **kwargs)
