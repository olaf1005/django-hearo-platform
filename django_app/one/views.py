import logging

from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

from haystack.models import SearchResult

from one.state import HearoOneState
from jawnmower.io import read_json_cache

from utils import JSON, render_appropriately

import settings.utils as setting_utils


logger = logging.getLogger(__name__)


def index(request):
    t = loader.get_template("one/index.html")

    # The SVG source for the world map
    # We just inject this right into the HTML
    # so that we can access the countries with JS
    mapsvg_fn = setting_utils.project_path("static/worldmap/map.svg")
    with open(mapsvg_fn, "r") as mapsvg_file:
        mapsvg = mapsvg_file.read()

    # Get cached world stats for the map
    countries, countries_json = read_json_cache("map.countries") or ([], "")
    coords, coords_json = read_json_cache("map.coords") or ([], "")

    state = HearoOneState(request.path)

    return render_appropriately(
        request,
        t,
        {
            "contentclass": "one",
            "pageclass": "full",
            "mapsvg": mapsvg,
            "countries": countries,
            "countries_json": countries_json,
            "coords_json": coords_json,
            # Global template option to show the filters button
            "1_filters": True,
            # Prepopulate UI's filters with any that are in the URL
            "filters": state.params,
        },
    )


def content_listings(request, path):
    offset = int(request.GET.get("offset", 0))
    count = int(request.GET.get("count", 20))
    search_query = request.GET.get("q", None)
    # Music filters
    ranking = request.GET.get("ranking", None)
    time = request.GET.get("time", None)
    price = request.GET.get("price", None)

    state = HearoOneState(path)

    results = state.results(
        {
            "offset": offset,
            "count": count,
            "search_query": search_query,
            # Music
            "ranking": ranking,
            "time": time,
            "price": price,
        }
    )

    context = {}

    if (
        isinstance(results, list)
        and len(results) > 0
        and isinstance(results[0], SearchResult)
    ):
        results = [x.object for x in results]

    context["listings"] = [c.as_music_listing(request) for c in results if c]

    context["counts"] = state.cached_noun_counts

    return JSON(context)


def path_from_filters(request):
    filters = request.GET.dict()
    state = HearoOneState(filters)
    return HttpResponse(state.to_URL())


def redirect_to_map(request):
    return HttpResponseRedirect("/")
