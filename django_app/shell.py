#!/usr/bin/env python
import datetime
import sys

import django

django.setup()

from django.conf import settings
from accounts.models import *
from media.models import *
from activity.models import *
from events.models import *
from feeds.models import *
from player.models import *
from search.models import *
from worldmap.models import *
from mail.models import *
import utils


try:
    try:
        from IPython import embed

        embed()
    except:
        # Older version?
        from IPython.Shell import IPShell

        shell = IPShell(argv=[], user_ns=locals())
        shell.mainloop()
except ImportError:
    print("Install ipython")
