import os
import sys
import logging
from logging.config import dictConfig


logging_config = dict(
    version=1,
    formatters={"basic": {"format": "%(asctime)s [%(levelname)s] %(message)s"}},
    handlers={
        "stream": {
            "class": "logging.StreamHandler",
            "formatter": "basic",
            "level": os.getenv("TARTAR_DEBUG_LEVEL", 10),
        },
        "rainbow": {
            "class": "rainbow_logging_handler.RainbowLoggingHandler",
            "stream": sys.stderr,
            "formatter": "basic",
            "level": os.getenv("TARTAR_DEBUG_LEVEL", 10),
        },
    },
    root={"handlers": [os.getenv("TARTAR_LOGGER", "stream")], "level": logging.DEBUG,},
)

dictConfig(logging_config)
