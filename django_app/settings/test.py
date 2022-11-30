from .dev import *

import os

INSTALLED_APPS += [
    "django_nose",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "hearo_test",
        "USER": os.getenv("PG_USER"),
        "PASSWORD": os.getenv("PG_PASS"),
        "HOST": os.getenv("PG_HOST"),
        "PORT": int(os.getenv("PG_PORT", 5432)),
    }
}

DEBUG = True
TEMPLATE_DEBUG = DEBUG
SERVER = False

ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = root_path("log", "email_outbox")

CONFIG = project_path(os.getenv("TARTAR_CONFIG", "dev.config"))

ENABLE_HTS = True

REQUIRE_VERIFICATION_FOR_LOGIN = False

HEARO_TEAM_PROFILE_ID = None

FILTER_GMAIL_SPECIAL_CHARS = False

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "PATH": os.path.join(root_path("tmp"), "whoosh_index"),
    },
}

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"
