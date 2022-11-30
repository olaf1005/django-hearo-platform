import datetime
import json
from django.contrib.auth.decorators import login_required

from geopy import geocoders

from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.template import loader

from accounts.models import Profile, Location
from events.models import Event

import utils


@login_required
def get_event(request):
    _id = request.GET["id"]
    view = request.user.person.view
    location = view.location.most_exact if view.location else ""
    event = Event.objects.get(id=_id)
    j = event.jsonify(request)
    j["profile"]["location"] = location
    fans = [fanevent.fanner.jsonify(request) for fanevent in event.fan_events.all()]
    return JsonResponse([j, fans], safe=False)


@login_required
def update(request):
    start = datetime.datetime.fromtimestamp(int(request.GET["start"]))
    end = datetime.datetime.fromtimestamp(int(request.GET["end"]))

    loc = request.GET["location"]

    events = Event.objects.filter(starts__gte=start, starts__lte=end)

    if request.user.is_authenticated and request.GET["filter"] == "Fan Events":
        view = request.user.person.view
        faned = [fan.fanee.id for fan in view.get_faned()]
        events = events.filter(Q(profile__in=faned) | Q(artists__in=faned)).distinct()

    if loc:
        events = utils.get_objects_near(Event, events, loc.replace("Venue: ", ""))
    events = events.order_by("starts")
    events = [event.jsonify(request) for event in events]
    return JsonResponse(events, safe=False)


@login_required
def edit_event_ajax(request):
    view = request.user.person.view
    # TODO: danielnordberg: error never used Wed Feb 25 17:07:25 EAT 2015
    error = False
    # TODO: danielnordberg: error_message never returned or used Wed
    # Feb 25 17:06:43 EAT 2015
    error_message = ""
    if request.method == "POST":
        rp = request.POST
        if not rp["title"]:
            error = True
            error_message += "You need a title! \n"
        if not rp["starts"]:
            error = True
            error_message += "You need to have a starting date! \n"
        title = rp["title"]
        # venue= rp['venue']
        # TODO implement events by their venues
        # TODO: danielnordberg: venue not used Wed Feb 25 17:08:27 EAT 2015
        venue = None
        description = rp["description"]
        starts = rp["starts"].strip()

        if request.POST.get("ends"):
            ends = rp["ends"].strip()
        else:
            ends = None

        event = None
        if request.POST["id"]:
            event = Event.objects.get(id=rp["id"])
            # DONT TRUST THE WEB
            if event.profile != view:
                return HttpResponse("This event isn't yours!!")
        g = geocoders.GoogleV3()
        loc = None
        eloc = rp["elocation"]

        if Location.objects.filter(most_exact=eloc).exists():
            loc = Location.objects.get(most_exact=eloc)
        else:
            try:
                place, (lat, lng) = (g.geocode(rp["elocation"], exactly_one=False))[0]
                loc, created = Location.objects.get_or_create(
                    lat=lat, lng=lng, most_exact=place
                )
            except:
                pass
        # TODO: remove this from model??
        iloc = ""
        if event:
            event.location_text = iloc
            event.title = title
            event.description = description
            event.starts = starts
            event.ends = ends
            event.location = loc
        else:
            event = Event.objects.create(
                ends=ends,
                location=loc,
                location_text=iloc,
                profile=view,
                starts=starts,
                title=title,
                description=description,
            )

    event.artists.clear()
    for artist_id in json.loads(rp["artists"]):
        artist = Profile.objects.get(id=artist_id)
        event.artists.add(artist)
    if "ticket_url" in rp:
        event.ticket_url = rp["ticket_url"]

    try:
        event.save()
    except:
        error_message += "Badly formatted date forms! expected: yyyy-mm-dd hh:mm"
    return HttpResponse(event.id)


def eventpage(request):
    t = loader.get_template("events/eventpage.html")
    if request.user.is_authenticated:
        if request.user.person.view.location:
            location = request.user.person.view.location.most_exact
        else:
            location = ""
    else:
        location = ""
    return utils.render_appropriately(
        request, t, {"location": location, "contentclass": "shows"}
    )
