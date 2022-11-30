# -*- coding: utf-8 -*-
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False
TEMPLATE_DEBUG = False
SERVER = True
REQUIRE_VERIFICATION_FOR_LOGIN = True

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
        "ENGINE": "haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine",
        "URL": "http://elasticsearch:9200/",
        "INDEX_NAME": "haystack",
    },
}

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
SENDGRID_API_KEY = EMAIL_HOST_PASSWORD
SENDGRID_EMAIL_VALIDATION_API_KEY = os.getenv("SENDGRID_EMAIL_VALIDATION_API_KEY")
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

ALLOWED_HOSTS = ["*"]

COMPRESS_OFFLINE = False

CONFIG = project_path(os.getenv("TARTAR_CONFIG", "prod.config"))

STRIPE_SECRET = os.getenv("STRIPE_SECRET")
STRIPE_KEY = os.getenv("STRIPE_KEY")

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

if not (TESTING or DEBUG):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        release=os.getenv("GIT_RELEASE"),
    )
