#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import os.path
import sys
import re

from .utils import root_path, project_path

# This needs to be imported into settings to configure recovery keys
from .keys import RECOVERY_OPENPGP_PUBLIC_KEYS


DEBUG = bool(int(os.getenv("DEBUG", 0)))

TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

BASE_URL = "tune.fm"

TWITTER_HANDLE = "tunefmofficial"
FACEBOOK_HANDLE = "tunefmofficial"
MEDIUM_HANDLE = "hearo-fm"

TIME_ZONE = "America/New_York"

LANGUAGE_CODE = "en-us"

SITE_ID = 2

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = root_path("media")

MEDIA_URL = ""

STATIC_ROOT = "/static/"

STATIC_URL = "/public/"

ADMIN_MEDIA_PREFIX = "/static/admin/"

# In production this should be BASE_URL
ALLOWED_HOSTS = ["*"]

STATICFILES_DIRS = (project_path("static"),)
FIXTURE_DIRS = (project_path("hearo_unittest/fixtures/"),)

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "PATH": root_path("whoosh_index"),
    },
}

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # "compressor.finders.CompressorFinder",
]

SECRET_KEY = "wmd464t)6jkcq*w9thvo+jtdh&o9*v62l9y9aa@vgcj9^)r)oo"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [project_path("templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django_settings_export.settings_export",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
    "login_required.LoginRequiredMiddleware",
]

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


ROOT_URLCONF = "urls"

ALLOWED_INCLUDE_ROOTS = ("",)

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_admin_bootstrapped",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django_user_agents",
    "haystack",
    "accounts",
    "activity",
    "payment_processing",
    "mail",
    "media",
    "events",
    "player",
    "support",
    "feeds",
    "common",
    "email_from_template",
    "one",
    "worldmap",
    "mathfilters",
    # "compressor",
    "django_inlinecss",
    "newsletter",
    "sorl.thumbnail",
    "formadmin",
]

COMPRESS_OFFLINE = False

COMPRESS_PRECOMPILERS = (("text/less", "lessc {infile}"),)

COMPRESS_FILTERS = {
    "css": ["compressor.filters.cssmin.CSSCompressorFilter",],
    "js": [
        "compressor.filters.jsmin.JSMinFilter",
        # Slimit is a bit buggy with .min.js files
        # 'compressor.filters.jsmin.SlimItFilter',
    ],
}

COMPRESS_PARSER = "compressor.parser.BeautifulSoupParser"

COMPRESS_ENABLED = os.environ.get("COMPRESS_ENABLED", True)

LOG_DB_QUERIES = bool(int(os.environ.get("DEBUG_DB", 0))) and ["dbdebug"] or []

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "clean": {"format": "%(message)s (%(lineno)s)", "datefmt": "%Y-%m-%d %H:%M:%S"},
        "request_log": {"format": "▶ %(message)s", "datefmt": "%Y-%m-%d %H:%M:%S"},
        "simple": {
            "format": "[%(asctime)s] [%(lineno)-5s] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": "[%(name)s][%(asctime)s] [%(levelname)-8s] - %(message)s (%(filename)s:%(lineno)s - %(funcName)s)",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "dbdebug": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "simple",
            "stream": sys.stderr,
        },
        "email_notifications": {
            "level": "INFO",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "payments": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "emails": {
            "level": "INFO",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "management.commands": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "clean",
            "stream": sys.stderr,
        },
        "tartar": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        # Warning messages are sent to admin emails
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "email_notifications": {"handlers": ["email_notifications"], "level": "INFO",},
        "sendemail_template": {"handlers": ["emails"], "level": "INFO",},
        "payments": {"handlers": ["payments"], "level": "DEBUG",},
        "django.db.backends": {
            "handlers": LOG_DB_QUERIES,
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {"handlers": ["mail_admins"], "propagate": False,},
        "accounts.management.commands": {
            "handlers": ["management.commands"],
            "propagate": False,
        },
        # Needed to stop ipython shell from spitting out debug messages
        "parso": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # Stop haystack messages and requests messages if not error
        "elasticsearch": {"level": "ERROR"},
        "caching": {"level": "ERROR"},
        "urllib3": {"level": "ERROR"},
        "": {"handlers": ["console"], "level": "DEBUG", "propagate": False,},
    },
}

LOGIN_URL = "/login/"

AUTHENTICATION_BACKENDS = (
    "backend.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
)

HEARO_TEAM_PROFILE_ID = 108

DATA_UPLOAD_MAX_NUMBER_FIELDS = None
DATA_UPLOAD_MAX_MEMORY_SIZE = None

UPLOADS_DIR = os.path.join(MEDIA_ROOT, "uploads")
DOWNLOADS_DIR = os.path.join(MEDIA_ROOT, "downloads")
STREAMS_DIR = os.path.join(MEDIA_ROOT, "streams")
IMAGES_DIR = os.path.join(MEDIA_ROOT, "images")
# sorl.thumbnails
IMAGE_CACHE_DIR = os.path.join(MEDIA_ROOT, "cache")
ALBUMART_DIR = os.path.join(MEDIA_ROOT, "albumart")
TMP_DIR = os.path.join(MEDIA_ROOT, "tmp")
ZIP_DIR = os.path.join(MEDIA_ROOT, "ziptemp")
MP3_STREAM_BITRATE = "192"

# TODO: review - we are keeping this since there is too much code that
# links to these variables and their related functions
STRIPE_PUBLISHABLE = 2.9
STRIPE_FEE_PERCENTAGE = 2.9
STRIPE_FEE_FLAT = 0.3
HEARO_FEE_PERCENTAGE = 10.0
TOTAL_PURCHASE_VALUE_SUSPICIOUS = 150
INDIVIDUAL_PURCHASE_VALUE_SUSPICIOUS = 10

MAX_SHORT_STRING_LENGTH = 20

CONFIG = project_path(os.getenv("TARTAR_CONFIG", "dev.config"))

# email_from_template configuration
EMAIL_CONTEXT_PROCESSORS = (
    "email_from_template.context_processors.debug",
    "email_from_template.context_processors.django_settings",
)

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"

S3_BUCKET = os.getenv("S3_BUCKET")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")

# Use sentry for error logs instead
ADMINS = (
    ("Daniel6", "dnordberg@gmail.com"),
    ("AndrewAntar", "andrewantar@gmail.com"),
    # ('Brian Antar', 'bantar07@gmail.com'),
    # ('Ben', 'gmbooking@gmail.com'),
)

REQUIRE_VERIFICATION_FOR_LOGIN = False

GOOGLE_MAPS_GEOCODING_API_KEY = os.getenv("GOOGLE_MAPS_GEOCODING_API_KEY")
YOUTUBE_DATA_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY")

NOTIFICATIONS_EMAIL = os.getenv(
    "NOTIFICATIONS_EMAIL", "notifications@{}".format(BASE_URL)
)

# Set if rethinkdb is setup to test media.Song.streaming_url
DEV_RETHINKDB_SETUP = bool(int(os.getenv("DEV_RETHINKDB_SETUP", "0")))

AUTH_EXEMPT_ROUTES = [
    re.compile(route)
    for route in [
        r"^favicon.ico",
        r"^admin/(.*)",
        r"^join/(.*)",
        r"^signup/",
        r"^about/(.*)",
        r"^password-recovery/(.*)",
        r"^not-verified/",
        r"^refresh-header/",
        r"^send-recovery/",
        r"^newsletter/(.*)",
        r"^verify/",
        r"^send-verification/",
        r"^privacy-policy/",
        r"^terms/",
        r"^copyright/",
        r"^artist-agreement/",
        r"^login/",
        r"^logout/",
        r"^register-ajax/",
        r"^robots.txt",
        r"^public/(.*)",
        r"^images/(.*)",
        r"^get-autocomplete/(.*)",
        r"^api/(.*)",
        r"^my-account/location-ajax/(.*)",
    ]
]
AUTH_LOGIN_ROUTE = "/signup/"

ENABLE_HTS = True

H_HTS_API_URL = os.getenv("H_HTS_API_URL")

# JAM required to listen to one minute of audio
JAM_PER_MINUTE = 0.2
# Value of each token for fiat display purposes
TOKEN_DOLLAR_VALUE = 0.05
# Decimal token multiplier, any jam values should be multiplied by (when
# performing transactions through the api) or divided by this number (when
# displaying the JAM value of tokens)
TOKEN_MULTIPLIER = 10 ** 8
DISABLE_STARTER_TOKENS = False
# Tokens granted to new users
NEW_USER_TOKENS = int(100 * TOKEN_MULTIPLIER)
# The first listen of a song will be free. This is the threshold that
# determines whether a user actually listened to a song
FREE_LISTEN_SECONDS = 0
# Percentage of tokens transferred back to hot wallet when
# users listen to songs
FACILITATION_PERCENTAGE = 0.1
# Sanebox or production (THIS SHOULD NEVER BE CHANGED)
PRIVATE_KEY_PLACEHOLDER = "PRIVATEKEY_PLACEHOLDER"
PRIVATE_KEY_SESSION_KEY = "hederaPrivateKey"

# Filter usage of . and + in gmail address
FILTER_GMAIL_SPECIAL_CHARS = True

# This is also the number of keys required to be set in
# settings/keys.py to generate permutations of the recovery keys
NUM_AUTHORIZERS_REQUIRED_FOR_PASSWORD_RESET = 2

# Not used (django-cryptography)
# CRYPTOGRAPHY_SALT = ''

SETTINGS_EXPORT = [
    "BASE_URL",
    "FACEBOOK_HANDLE",
    "FACILITATION_PERCENTAGE",
    "HEARO_TEAM_PROFILE_ID",
    "JAM_PER_MINUTE",
    "MEDIUM_HANDLE",
    "NEW_USER_TOKENS",
    "NUM_AUTHORIZERS_REQUIRED_FOR_PASSWORD_RESET",
    "TOKEN_DOLLAR_VALUE",
    "TWITTER_HANDLE",
    "DEBUG",
]

TESTS_IN_PROGRESS = False
if "test" in sys.argv[1:] or "jenkins" in sys.argv[1:]:
    DEBUG = False
    TEMPLATE_DEBUG = False
    TESTS_IN_PROGRESS = True

INTERNAL_IPS = (
    "127.0.0.1",
    "0.0.0.0",
)

# giving a song a large hotness value will likely get the
# artist and album featured as well, so better to
# put splash_featured for artists than individual songs
# or significantly reduce the values spash value here
SPLASH_FEATURED_SONG_HOTTNESS_VALUE = 100
SPLASH_FEATURED_ARTIST_HOTTNESS_VALUE = 100
SPLASH_FEATURED_ALBUM_HOTTNESS_VALUE = 100

DEC_LOADER = "utils.custom_email_domain_loader"

# Most of this is replaced in settings env, e.g prod, dev

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

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
SENDGRID_API_KEY = EMAIL_HOST_PASSWORD
SENDGRID_EMAIL_VALIDATION_API_KEY = os.getenv("SENDGRID_EMAIL_VALIDATION_API_KEY")
QUICKEMAILVERIFICATION_API_KEY = os.getenv("QUICKEMAILVERIFICATION_API_KEY")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"

# Test if its working from a host, telnet 10.183.24.164 11211, type stats, then
# quit
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": os.getenv("MEMCACHED_HOST"),
    }
}

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine",
        "URL": "http://{}/".format(os.getenv("ELASTICSEARCH_HOST")),
        "INDEX_NAME": "haystack",
    },
}

ALLOWED_HOSTS = ["tune.fm", "localhost"]

CONFIG = project_path(os.getenv("TARTAR_CONFIG", "prod.config"))

ENABLE_HTS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "clean": {"format": "%(message)s (%(lineno)s)", "datefmt": "%Y-%m-%d %H:%M:%S"},
        "request_log": {"format": "▶ %(message)s", "datefmt": "%Y-%m-%d %H:%M:%S"},
        "simple": {
            "format": "[%(asctime)s] [%(lineno)-5s] --- %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": "[%(asctime)s] [%(levelname)-8s] - %(message)s (%(filename)s:%(lineno)s - %(funcName)s)",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "console": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "dbdebug": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "simple",
            "stream": sys.stderr,
        },
        "email_notifications": {
            "level": "INFO",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "payments": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "emails": {
            "level": "INFO",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "worldmap.compile_map_stats": {
            "level": "INFO",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        "management.commands": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "simple",
            "stream": sys.stderr,
        },
        "tartar.tartar_daemon": {
            "level": "DEBUG",
            "class": DEBUG
            and "rainbow_logging_handler.RainbowLoggingHandler"
            or "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
        },
        # Warning messages are sent to admin emails
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "email_notifications": {"handlers": ["email_notifications"], "level": "INFO",},
        "sendemail_template": {"handlers": ["emails"], "level": "INFO",},
        "worldmap.compile_map_stats": {
            "handlers": ["worldmap.compile_map_stats"],
            "level": "INFO",
        },
        "payments": {"handlers": ["console", "payments"], "level": "INFO",},
        "django.db.backends": {
            "handlers": LOG_DB_QUERIES,
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "INFO",
            "propagate": True,
        },
        "accounts.management.commands.bulk_import": {
            "handlers": ["management.commands"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Default
        "": {"handlers": ["console"], "level": "INFO", "propagate": False,},
    },
}
