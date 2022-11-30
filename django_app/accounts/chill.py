from accounts.models import Person
from utils import JSON
from django.db.models import Q


def query(request):
    "Returns profiles matching query"
    try:
        logged_in = request.user.person.view
    except:
        return JSON([])
    q = request.GET.get("query")

    exactQ = (
        Q(profile__name__iexact=q)
        | Q(user__first_name__iexact=q)
        | Q(user__last_name__iexact=q)
        | Q(profile__keyword__iexact=q)
    )
    prefixQ = (
        Q(profile__name__istartswith=q)
        | Q(user__first_name__istartswith=q)
        | Q(user__last_name__istartswith=q)
        | Q(profile__keyword__istartswith=q)
    )
    substringQ = (
        Q(profile__name__icontains=q)
        | Q(user__first_name__icontains=q)
        | Q(user__last_name__icontains=q)
        | Q(profile__keyword__icontains=q)
    )
    # matches (each holds more relevant results than the next)
    exactM = Person.objects.filter(exactQ)
    prefixM = Person.objects.filter(prefixQ & ~exactQ)
    substringM = Person.objects.filter(substringQ & ~prefixQ)

    # filter - not already in pending / members / admin
    all = [a.order_by("-profile__rank_all") for a in [exactM, prefixM, substringM]]
    exactM, prefixM, substringM = [list(a) for a in all]
    people = exactM[:20] + prefixM[:10] + substringM[:10]

    return JSON([p.profile.jsonify(request) for p in people])
