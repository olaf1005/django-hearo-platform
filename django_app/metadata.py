"""Musicbrainz unfortunately does seem to have a complete ISRC database.

The most complete ISRC lookup database seems to be isrcsearch and
for which querying is difficult and they don't provide an API.

Here I've copied the curl command from Google Chome then used
https://curl.trillworks.com to convert it into a query to fetch
the relevant metadata.

"""
import logging
import json

import requests


logger = logging.getLogger(__name__)


def get_metadata_by_isrc(isrc):
    """Returns something like this:
    {
    "numberOfHits":1,
    "displayDocs":[
        {
            "duration":"3:47",
            "recordingVersion":"",
            "recordingYear":"2019",
            "artistName":"Solange",
            "isrcCode":"USA2P1940768",
            "documentType":"recording",
            "showReleases":true,
            "releaseLabel":"Music World Music",
            "upcCode":"192641345845",
            "releaseDate":"2003-01-21",
            "releaseName":"Solo Star",
            "releaseArtist":"Solange",
            "trackTitle":"Bring It on Home",
            "id":"TRK46500712"
        }
    ]
    }
    """
    try:
        headers = {
            "sec-fetch-mode": "cors",
            "origin": "https://isrcsearch.ifpi.org",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cookie": "csrftoken=h5flgHEmaxxRbbqbArcrcbdkqi4W8TrsCNAX57ihz9nJiE9Nch3rICtNXupW95p3; sessionid=d0qigsl451uk80rp789xf2b24va2fhc2; __utma=262412820.254435534.1568628341.1568628341.1568628341.1; __utmc=262412820; __utmz=262412820.1568628341.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); OptanonAlertBoxClosed=2019-09-16T10:10:39.857Z; _ga=GA1.2.810818982.1568628664; _gid=GA1.2.1791022574.1568628664; OptanonConsent=landingPath=NotLandingPage&datestamp=Mon+Sep+16+2019+13%3A15%3A29+GMT%2B0300+(East+Africa+Time)&version=4.8.0&EU=false&groups=1%3A1%2C2%3A1%2C3%3A1%2C4%3A1%2C0_31741%3A1%2C0_31742%3A1&consentId=558685ee-a759-4e8e-a183-0f8088bd3b62&AwaitingReconsent=false; __utmb=262412820.3.9.1568628639848",
            "x-csrftoken": "Y0dSOzkCuuaI9NwY5qb1WTlRELBAAcHxjIyuDZYxT60AggfAHg21skBkbXWABoF8",
            "pragma": "no-cache",
            "x-newrelic-id": "XQQAV1VaGwIGXFJaAQcD",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
            "content-type": "application/json;charset=UTF-8",
            "accept": "application/json, text/plain, */*",
            "cache-control": "no-cache",
            "authority": "isrcsearch.ifpi.org",
            "referer": "https://isrcsearch.ifpi.org/",
            "sec-fetch-site": "same-origin",
            "dnt": "1",
        }

        data = '{"searchFields":{"isrcCode":"USSM10201932"},"showReleases":0,"start":0,"number":10}'

        response = requests.post(
            "https://isrcsearch.ifpi.org/api/v1/search", headers=headers, data=data
        )
    except Exception as e:
        logger.error(e)
