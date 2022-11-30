from random import randint

import django

django.setup()

from accounts.models import *
from media.models import *


models = [Profile, Song, Album]


for model in models:
    for obj in model.objects.all():
        obj.rank_all = randint(0, 500)
        obj.rank_today = randint(0, 500)
        obj.rank_week = randint(0, 500)
        obj.rank_month = randint(0, 500)
        obj.rank_year = randint(0, 500)
        obj.save()
    print("DONE {}!".format(model.__name__))
