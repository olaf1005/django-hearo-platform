from .base import *

import os

# Test if its working from a host, telnet 10.183.24.164 11211, type stats, then
# quit
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",}}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("PG_DB_NAME"),
        "USER": os.getenv("PG_USER"),
        "PASSWORD": os.getenv("PG_PASS"),
        "HOST": os.getenv("PG_HOST"),
        "PORT": int(os.getenv("PG_PORT", 5432)),
    }
}

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine",
        "URL": "http://{}/".format(os.getenv("ELASTICSEARCH_HOST")),
        "INDEX_NAME": "haystack",
        # 'TIMEOUT': 60
    },
}

DEBUG = True
TEMPLATE_DEBUG = DEBUG
SERVER = False

ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = root_path("log", "email_outbox")

CONFIG = project_path(os.getenv("TARTAR_CONFIG", "dev.config"))

# smclean@gmail.com's test keys
STRIPE_SECRET = os.getenv("STRIPE_SECRET")
STRIPE_PUBLISHABLE = os.getenv("STRIPE_PUBLISHABLE")

ENABLE_HTS = bool(os.getenv("ENABLE_HTS", 1))

REQUIRE_VERIFICATION_FOR_LOGIN = True

# Set this to
# HEARO_TEAM_PROFILE_ID = 108
# in local.py
# if your using a copy of the prod db
HEARO_TEAM_PROFILE_ID = None

FILTER_GMAIL_SPECIAL_CHARS = False

COMPRESS_ENABLED = False

# Add to settings/local.py if you wish to enable
# INSTALLED_APPS += [
#     "django_extensions",
# ]

# NOTEBOOK_ARGUMENTS = [
#     "--ip",
#     "0.0.0.0",
#     "--port",
#     "8001",
#     "--allow-root",
#     "--no-browser",
#     "--notebook-dir",
#     "/notebooks/",
#     "--NotebookApp.iopub_data_rate_limit=10000000",
# ]

# LOGGING['loggers']['django.db.backends'] = {
#     'level': 'DEBUG',
#     'handers': ['console'],
# }

# DEV_RETHINKDB_SETUP = True
