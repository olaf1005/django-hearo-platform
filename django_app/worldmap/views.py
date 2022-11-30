import re
import requests
from urllib.parse import urlencode
from worldmap.geography import COUNTRIES
from accounts.models import Profile
from django.conf import settings


# Helper methods for the world map.

# Provides utilities that use the Google Maps API to get
# detailed information on addresses given by users.


def query_Google_Maps_API(address):
    """
    <= Give an address query string of any level of specificity
    => Get all the data Google has on it in a dict
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json?%s&sensor=false&key=%s" % (
        urlencode({"address": address}),
        settings.GOOGLE_MAPS_GEOCODING_API_KEY,
    )
    response = requests.get(url)
    results = response.json()["results"]

    if len(results) > 0:
        return results[0]
    else:
        return None


def get_country(address):
    """
    <= Give an address query string of any level of specificity
    => If a country is found, get a dict:
        {
        "name": country name
        "code": two-letter country code
        }
    => If no country is found, None
    """

    address = str(re.sub(r"[^a-zA-Z\s]", "", address))

    data = query_Google_Maps_API(address)
    components = data["address_components"]
    if components:
        country = [x for x in components if "country" in x["types"]][0]
        if country:
            return {"name": country["long_name"], "code": country["short_name"]}
    return None


def get_secondary(address):
    """
    This is used for directory permalinks on specific coordinates.
    Gives us the best semantic representation of a place.
    """

    address = str(re.sub(r"[^a-zA-Z\s]", "", address))

    data = query_Google_Maps_API(address)
    if data:
        components = data["address_components"]
        if components:
            locality = [x for x in components if "locality" in x["types"]]
            admin1 = [
                x for x in components if "administrative_area_level_1" in x["types"]
            ]
            admin2 = [
                x for x in components if "administrative_area_level_2" in x["types"]
            ]
            country = [x for x in components if "country" in x["types"]]
            colloquial = [x for x in components if "colloquial_area" in x["types"]]

            # We need all sorta different attributes to make sure we do a
            # thorough job.  Get everything available.

            if admin1 != []:
                admin1 = admin1[0]
            else:
                admin1 = None

            if admin2 != []:
                admin2 = admin2[0]
            else:
                admin2 = None

            if locality != []:
                locality = locality[0]

            if country != []:
                country = country[0]
            else:
                country = None

            if colloquial != []:
                colloquial = colloquial[0]
            else:
                colloquial = None

            # Address formatting is complicated.

            if country:
                # For the US, abbreviate state names if we have a city, too
                if country["long_name"] == "United States":
                    if locality:
                        # City, state
                        # Example: Seattle, WA
                        return "%s, %s" % (locality["long_name"], admin1["short_name"])

                    elif admin1:
                        # State
                        # Example: Kentucky
                        return admin1["long_name"]

                    elif colloquial:
                        # Area names
                        # Example: Greater St. Louis
                        return colloquial["long_name"]

                elif country["long_name"] == "United Kingdom":
                    # Its country is listed as "United Kingdom"
                    # and admin1 is "England" because it also contains part of
                    # Northern Ireland.  So ditch the UK name and just go with
                    # England or Ireland.
                    if admin2 and admin1:
                        return "%s, %s" % (admin2["long_name"], admin1["short_name"])
                    elif admin1:
                        return admin1["long_name"]

                else:
                    # For any other country, spell out the city and country
                    # names using whatever we can get. Locality is preferred.
                    if locality:
                        return "%s, %s" % (locality["long_name"], country["long_name"])
                    elif admin1:
                        return "%s, %s" % (admin1["long_name"], country["long_name"])

            # Absolute last resorts.
            if colloquial:
                return colloquial["long_name"]

            elif locality:
                return locality["long_name"]

            else:
                return ""


def world_data():
    """
    Returns a dictionary of countries and the number of users in each country.

    >> world_data()
    {'AR': [1, 'Argentina'],
    'AT': [1, 'Austria'],
    'AU': [4, 'Australia'],
    'BJ': [1, 'Benin'],
    'BO': [1, 'Bolivia'],
    'BR': [1, 'Brazil'],
    'BW': [1, 'Botswana'],
    ...

    """
    all_users = Profile.objects.all().count()
    l = {"GLOBAL": [all_users]}
    profiles = Profile.objects.filter(location_set=True)
    for p in profiles:
        loc = p.location
        cty = str(loc.country)
        if cty:
            if cty in l:
                l[cty][0] += 1
            else:
                l[cty] = [1, COUNTRIES[cty]]
    return l
