default_app_config = "support.apps.SupportConfig"


class PasswordResetRequestStatus:
    APPROVED = "approved"
    PASSWORD_RESET = "password reset"
    PENDING_APPROVAL = "pending approval"
    REQUEST_DENIED = "request denied"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"

    CHOICES = (
        (APPROVED, "Approved"),
        (PASSWORD_RESET, "Password reset"),
        (PENDING_APPROVAL, "Pending approval"),
        (REQUEST_DENIED, "Request denied"),
        (UNVERIFIED, "Unverified"),
        (VERIFIED, "Verified"),
    )


class GeneralRequestStatus:
    PENDING = "pending"
    NEEDS_MORE_INFO = "needs more info"
    FIXED = "fixed"
    REQUEST_DENIED = "request denied"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    CANT_FIX = "cant fix"

    CHOICES = (
        (PENDING, "Pending"),
        (NEEDS_MORE_INFO, "Needs more info"),
        (FIXED, "Fixed"),
        (REQUEST_DENIED, "Request denied"),
        (UNVERIFIED, "Unverified"),
        (VERIFIED, "Verified"),
        (CANT_FIX, "Can't fix"),
    )


class GeneralRequestType:
    MUSIC_UPLOAD = "music upload"
    PRIVACY = "privacy"
    MUSIC = "music"
    IMAGES = "images"
    PROFILES = "profiles"

    CHOICES = (
        (MUSIC_UPLOAD, "Music upload"),
        (PRIVACY, "Privacy"),
        (MUSIC, "Music"),
        (IMAGES, "Images"),
        (PROFILES, "Profiles"),
    )
