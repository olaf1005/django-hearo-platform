# Download Daemon runner
#   usage: python down_run.py
#
import os
import logging
import tartar.logger

from infrared import Context
from hservices import Timberlake


logger = logging.getLogger("tartar.down_run")


def main():
    context = os.environ.get("TARTAR_CONFIG")
    down = Timberlake(Context(context))
    down.run()


if __name__ == "__main__":
    logging.info("Daemon is starting")
    if bool(int(os.environ.setdefault("IPDB_DEBUG", "0"))):
        from ipdb import launch_ipdb_on_exception

        with launch_ipdb_on_exception():
            main()
    else:
        main()
