"""
Data structure for storing Hearo states
Serializes them into and parses them from permalink URLs

Possible filters:
    noun
    location
    genre
    instrument

URL structures:
    /%keyword/
    A profile URL using the profile keyword
    Notes
        These URLs have precedance

    /{ location }/{ noun }/{ genre }/{ instrument }/
    A Hearo One map URL
    All params optional, but in this order always

"""

import re

from haystack.query import SearchQuerySet

from worldmap.geography import COUNTRIES_PARAMETERIZED, COUNTRY_CODES
from accounts.models import Location, Genre, Instrument

from utils import parameterize, unparameterize


ORDERED_URL_PARAMS = ["location", "noun", "sub_noun", "genre", "instrument"]
NOUNS = ["songs", "artists", "albums"]
SUB_NOUNS = [
    "bands",
    "musicians",
    "fans",
    "producers",
    "venues",
    "songwriters",
    "djs",
    "sound engineers",
    "teachers",
    "labels",
    "looking for a band",
]


class HearoOneState:
    """
    HearoOneState class for generating and parsing Hearo One URLs

    I/P:
        Either a string URL, or a dict of params

    Main methods:
        get(param)
        toURL()
    """

    ROOT = "/"

    def __init__(self, arg):
        self.params = {}
        self.cached_noun_counts = {}
        self._matchers = {
            "noun": self._match_for_noun,
            "sub_noun": self._match_for_sub_noun,
            "location": self._match_for_location,
            "genre": self._match_for_genre,
            "instrument": self._match_for_instrument,
        }

        if type(arg) in [str]:
            url = self._strip(arg)
            segments = url.split("/")
            for segment in segments:
                self._parse(segment)
        elif type(arg) == dict:
            self.from_params(arg)

    def set(self, param, val):
        self.params[param] = val

    def get(self, param):
        return self.params.get(param)

    def get_parameterized(self, param):
        if param == "location":
            location = self.get("location")
            if location:
                location = location.replace(" ", "-")
                location = location.replace(",-", ",")
            return location
        else:
            return parameterize(self.get(param))

    # URL parsing and helpers

    def from_params(self, params):
        for key in ORDERED_URL_PARAMS:
            if key in params:
                self.set(key, params[key])

    def _parse(self, segment):
        # Returns the params after the last param we find
        # that we already have set in self.params.
        to_search = [x for x in ORDERED_URL_PARAMS if x not in list(self.params.keys())]
        for param in to_search:
            matches = self._matchers[param](segment)
            if matches:
                self.set(param, matches)
                break

    # Parsing helpers

    def _match_for_noun(self, segment):
        # Determine if URL contains noun, and which one.
        # Saves and returns it
        return [part for part in segment.split("-") if part in NOUNS]

    def _match_for_sub_noun(self, segment):
        # Determine if URL contains noun, and which one.
        # Saves and returns it
        for noun in SUB_NOUNS:
            if parameterize(noun) == segment:
                return segment

    def _match_for_location(self, segment):
        # Don't match keyword 'all'
        if segment == "all" or segment == "":
            return
        segments = [x.strip() for x in segment.split(",")]
        if len(segments) == 1:
            parameterized_values = list(COUNTRIES_PARAMETERIZED.values())
            if segment in parameterized_values:
                rotated = dict(
                    list(
                        zip(parameterized_values, list(COUNTRIES_PARAMETERIZED.keys()))
                    )
                )
                return rotated[segment]
            possible_location = segments[0]
        else:
            segments[0] = segments[0].replace("-", " ")
            possible_location = ", ".join(segments)
            if segments[1] in COUNTRY_CODES:
                location1 = Location.objects.filter(
                    city=segments[0], country=COUNTRY_CODES[segments[1]]
                )
                if location1.exists():
                    return possible_location

        location2 = Location.objects.filter(most_exact=possible_location)
        location3 = Location.objects.filter(secondary=possible_location)

        if location2.exists() or location3.exists():
            return possible_location

    def _match_for_genre(self, segment):
        # Don't match keyword 'all'
        if segment == "all" or segment == "":
            return
        genre_attempt = Genre.objects.filter(slug=segment)
        if genre_attempt.exists():
            return genre_attempt[0].name

    def _match_for_instrument(self, segment):
        # Don't match keyword 'all'
        if segment == "all" or segment == "":
            return
        instrument_attempt = Instrument.objects.filter(slug=segment)
        if instrument_attempt.exists():
            return instrument_attempt[0].name

    def _strip(self, url):
        return re.sub(r"(^\/|\/$)", "", url)

    def _params_in_order(self):
        params = [self.get_parameterized(x) for x in ORDERED_URL_PARAMS]
        return [x for x in params if x]

    def to_URL(self):
        return "%s%s%s" % (
            self.ROOT,
            "/".join(self._params_in_order()),
            "/" if list(self.params.keys()) else "",
        )

    # Getting objects

    def results(self, opts):
        # EXTEND IT
        default = {"offset": 0, "count": 20, "search_query": None, "ranking": "hottest"}
        default.update(opts)
        opts = default
        return self.matching_objects(opts)

    def matching_objects(self, opts):
        searchq = opts.get("search_query", None)
        qs = SearchQuerySet()

        if searchq is None:
            qs = qs.all()
        else:
            qs = qs.auto_query(searchq)

        filter_map = {
            "musicians": lambda qs: qs.filter(is_musician=True),
            "fans": lambda qs: qs.filter(is_musician=False),
            "bands": lambda qs: qs.filter(is_band=True),
            "venues": lambda qs: qs.filter(is_venue=True),
            "djs": lambda qs: qs.filter(dj=True),
            "producers": lambda qs: qs.filter(is_producer=True),
            "sound engineers": lambda qs: qs.filter(is_engineer=True),
            "teachers": lambda qs: qs.filter(teacher=True),
            "songwriters": lambda qs: qs.filter(write_music=True),
            "looking for a band": lambda qs: qs.filter(join_band=True),
            "labels": lambda qs: qs.filter(is_label=True),
        }

        noun_list = self.get("noun")
        if noun_list:
            content_type_map = {
                "artists": "accounts.profile",
                "songs": "media.song",
                "albums": "media.album",
            }
            new_content_types = [content_type_map[x] for x in noun_list]
            qs = qs.filter(django_ct__in=new_content_types)

        sub_noun = self.get("sub_noun")
        if sub_noun:
            sub_noun = sub_noun.replace("-", " ")
            qs = filter_map[unparameterize(sub_noun)](qs)

        loc = self.get("location")
        if loc:
            qs = (
                qs.filter(location__icontains=loc)
                | qs.filter(location_country__icontains=loc)
                | qs.filter(secondary_location__icontains=loc)
            )

        genre = self.get("genre")
        if genre:
            qs = qs.filter(genres__in=[genre])

        inst = self.get("instrument")
        if inst:
            qs = qs.filter(instruments__in=[inst])

        if opts["ranking"] == "hottest":
            qs = qs.order_by("-rank_%s" % opts["time"])
        else:
            qs = qs.order_by("-created")

        for f in filter_map:
            self.cached_noun_counts[f] = filter_map[f](qs).count()

        if opts["offset"] == 0:
            return qs[opts["offset"] : opts["offset"] + opts["count"]]
        else:
            return qs[opts["offset"] + 1 : opts["offset"] + 1 + opts["count"]]
