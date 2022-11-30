from django.db.models import Q
from django.contrib.auth.decorators import login_required

from accounts.models import Profile, Person, Organization

from utils import JSON


def query_artists(request):
    "for use in events (artists playing)"
    # view = request.user.person.view

    # geo_dist = view.geo_dist
    q = request.GET["query"]
    # eventid = request.GET['eventid'] if 'eventid' in request.GET else False
    if q:
        profiles = Profile.objects.filter(
            Q(_person__is_musician=True) | Q(organization__is_band=True)
        )
        # Don't include people who have chosen to not show up in search
        profiles = profiles.filter(profile_private=False).order_by("-rank_all")

        exactQ = Q(name__iexact=q) | Q(keyword__iexact=q)
        prefixQ = Q(name__istartswith=q | Q(keyword__istartswith=q))
        substringQ = Q(name__icontains=q) | Q(keyword__icontains=q)
        exactM = profiles.filter(exactQ)
        prefixM = profiles.filter(prefixQ & ~exactQ)
        substringM = profiles.filter(substringQ & ~prefixQ)
        l = list(exactM[:20]) + list(prefixM[:10]) + list(substringM[:10])
    else:
        l = []
    all_profiles = [o.jsonify(request) for o in l]
    if all_profiles:
        return JSON({"status": True, "error": None, "data": {"people": all_profiles}})
    else:
        # Return status False if no results available
        return JSON({"status": False, "error": None, "data": {"people": []}})


@login_required
def query_inviteable(request):
    "for use when inviting users to hearo"

    orgid = request.GET.get("groupid", request.user.person.view.organization.id)
    org = Organization.objects.get(pk=int(orgid))

    # geo_dist = view.geo_dist
    q = request.GET["query"]
    if q:
        # get results from database
        # queries (each is a superset of the next)
        # filter by name (first or last)
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
        all = [
            a.exclude(profile___person__in=org.pending.all())
            .exclude(profile___person__in=org.members.all())
            .order_by("-profile__rank_all")
            for a in [exactM, prefixM, substringM]
        ]
        exactM, prefixM, substringM = [list(a) for a in all]
        people = exactM[:20] + prefixM[:10] + substringM[:10]
    else:
        people = []

    all_people = []
    for person in people:
        if person.profile != request.user.profile:
            all_people.append(person.profile.jsonify(request))

    if all_people:
        return JSON({"status": True, "error": None, "data": {"people": all_people}})
    else:
        # Return status False if no results available
        return JSON({"status": False, "error": None, "data": {"people": []}})
