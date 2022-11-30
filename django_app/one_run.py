# Process uploads Daemon runner
#   usage: python one_run.py
#
import os
import logging
import tartar.logger

from infrared import Context
from hservices import OneDirection


logger = logging.getLogger("tartar.one_run")


def main():
    context = os.environ.get("TARTAR_CONFIG")
    one = OneDirection(Context(context))
    one.run()


if __name__ == "__main__":
    logging.info("Daemon is starting")
    if bool(int(os.environ.setdefault("IPDB_DEBUG", "0"))):
        from ipdb import launch_ipdb_on_exception

        with launch_ipdb_on_exception():
            main()
    else:
        main()
