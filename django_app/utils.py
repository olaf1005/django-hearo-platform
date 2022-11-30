""" helper functions """
import base64
import collections
import datetime
import hashlib
import json
import logging
import random
import re
import smtplib
import string
import unicodedata as ud
from functools import reduce, wraps
from io import BytesIO

import django
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.template import Context, NodeList
from django.template.loader_tags import BlockNode, ExtendsNode
from django.views.generic import TemplateView
from email_from_template import send_mail
from geopy import geocoders
from PIL import Image, ImageOps

from disposable_email_checker.emails import email_domain_loader

latin_letters = {}


email_re = re.compile(
    # dot-atom
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
    # quoted-string
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'
    r")@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$",
    re.IGNORECASE,
)  # domain


def custom_email_domain_loader():
    # Anyone still using AOL will be too much of a customer service burden
    return [
        "zoobug.org",
        "hotmail.red",
        "suprmailer.uno",
        "bobsmail.site",
        "free2mail.xyz",
        "molman.top",
        "mailboxmaster.info",
        "mailsugo.buzz",
        "man2man.xyz",
        "dummymails.cc",
        "veona.pw",
        "pgyu.xyz",
        "aiafhg.com",
        "tchoeo.com",
        "stocksaa318.xyz",
        "txtee.site",
        "trashmail.tk",
    ] + email_domain_loader()


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class ExtraContextTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _update_default_context(context)
        return context


def ago(date):
    # Returns a semantic string telling you how long ago a datetime object was
    now = datetime.date.today()
    raw_now = 365 * now.year + 30 * now.month + now.day
    raw_date = 365 * date.year + 30 * date.month + date.day
    raw = raw_now - raw_date
    if raw == 0:
        return "today"
    if 0 < raw <= (365 / 12):
        weeks = int(raw / 7)
        if weeks:
            return "%s week%s ago" % (weeks, "s" if weeks > 1 else "")
        else:
            return "%s day%s ago" % (raw, "s" if raw > 1 else "")
    elif raw <= 365:
        months = raw / (365 / 12)
        return "%s month%s ago" % (months, "s" if months > 1 else "")
    return None


def file_exists(obj):
    # Check whether actual file of FileField exists (is not deleted / moved out).
    if obj:
        return obj.storage.exists(obj.name)
    return False


def trim_name(full_name):
    if len(full_name) > settings.MAX_SHORT_STRING_LENGTH:
        short_name = full_name[: (settings.MAX_SHORT_STRING_LENGTH - 3)] + "..."
    else:
        short_name = full_name
    return short_name


def is_latin(uchr):
    try:
        return latin_letters[uchr]
    except KeyError:
        return latin_letters.setdefault(uchr, "LATIN" in ud.name(uchr))


def only_roman_chars(unistr):
    return all(is_latin(uchr) for uchr in unistr if uchr.isalpha())


def normalize_email(email, remove_period=True):
    # Get just the name portion
    if "@gmail.com" in email:
        email = email.strip().split("@gmail.com")[0]
        if remove_period:
            email = email.replace(".", "")
        # Remove the part after +
        if "+" in email:
            email = email.split("+")[0]
        # Return email formated correctly
        return "{}@gmail.com".format(email)
    elif "@protonmail.com" in email:
        email = email.strip().split("@protonmail.com")[0]
        if remove_period:
            email = email.replace(".", "")
        # Remove the part after +
        if "+" in email:
            email = email.split("+")[0]
        # Return email formated correctly
        return "{}@protonmail.com".format(email)
    else:
        return email


def ajax_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        return view(request, *args, **kwargs)

    return wrapper


def ajax_login_required_no_error(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse(status=200)
        return view(request, *args, **kwargs)

    return wrapper


def get_profile(user):
    "Get profile or return None"
    if user.is_anonymous:
        return None
    else:
        return user.profile


# '!@#$%^&*()_+'
WHITELIST_BASH_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "abcdefghijklmnopqrstuvwxyz" + "1234567890" + "_"
)


def parameterize(s):
    try:
        return re.sub(r"[\s]", "-", s)
    except:
        return None


def unparameterize(s):
    try:
        return re.sub(r"-", " ", s)
    except:
        return None


def assert_valid_acctype(acctype):
    assert acctype in ["fan", "artist", "venue", "band", "label"]


def get_session_info(request):
    """
    called from switch account, returns a dict representing all the accounts
    you can switch to
    """
    person = profile = accounts = None
    if request.user.is_authenticated:
        person = request.user.person
        profile = person.view.jsonify(request)
        accounts = [prof.jsonify(request) for prof in person.get_accounts()]
    return {
        "profile": profile,
        "accounts": accounts,
        "mail_count": person.view.get_unread().count() if person else 0,
    }


def image_operation(
    reqFile,
    filename,
    isNew=True,
    ops=None,
    size=(550, 550),
    cropCenter=(0.5, 0.3),
    coords=(0, 0, 0, 0),
):
    """
    image_operation
    takes in an image file, performs some operations, then returns as a saved
    file options:
    'none' - perform no operation
    'thumbnail' - resize the image to within a certain size (size) while
    maintaining its dimensions
    'crop_center' - crop the image to a certain size (size) around a center,
    cropCenter
    'crop_coords' - crop the image around specific coordinates, coords
    arguments:
    reqFile - the request
    filename - title to be appended to the filename of the photo
    isNew - boolean True if image is a new upload, and False if already in
    database
    ops - an array of string names of operations to perform on photo
    size - tuple (width, height) size of the resulting photo
    cropCenter - tuple (width, height) center of crop area
    """
    # is image a new upload or already in database?
    image = Image.open(reqFile)

    if ops is None:
        ops = []

    # perform operations
    for op in ops:
        if op == "thumb":
            image.thumbnail(size, Image.ANTIALIAS)
        elif op == "crop_center":
            image = ImageOps.fit(image, size, Image.ANTIALIAS, centering=cropCenter)
        elif op == "crop_coords":
            image = image.crop(coords)

    # If not a png or jpg, convert
    if image.mode != "RGB":
        image = image.convert("RGB")

    thumb_io = BytesIO()
    image.save(thumb_io, format="JPEG", quality=90)

    filename = hashlib.md5(image.tobytes()).hexdigest() + "-" + filename + ".jpg"

    return InMemoryUploadedFile(
        ContentFile(thumb_io.getvalue()),
        None,
        filename,
        "image/jpeg",
        thumb_io.tell,
        "utf-8",
    )


def sendemail(subject, to, message):
    """
    sends an email from the server

    subject : string, to : string, message : string => .
    e.g. sendemail("hello world", "hearofm@googlegroups.com", "hearo's first
    email!")
    note: message is piped to stdin. sanitize! use templates and only insert
    simple things like names into it. validate & sanitize the message. qmail is
    secure but we must be paranoid and assume it's insecure.
    """
    logger = logging.getLogger("default")
    logger.info("Sending email [%s] to %s", subject, to)

    try:
        django.core.mail.send_mail(
            subject,
            message,
            "feedback@{}".format(settings.BASE_URL),
            [to],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.exception("Error sending contact email: %s", e)
        return False


def sendemail_template(receivers, template, context):
    logger = logging.getLogger("sendemail_template")
    logger.info("Sending email [%s] to %s", template, receivers)

    _update_default_context(context)

    try:
        send_mail(
            receivers, template, context, "notifications@{}".format(settings.BASE_URL)
        )
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.exception("Error sending [%s] to [%s]: %s", template, receivers, e)
        return False


def ensure_unique_keyword(key, model):
    """
    ensures that a keyword is unique
    input: key - original keyword, model - the model of the object with keyword
    output : new key making sure no other object share the keyword
    TODO: make uniqueness less arbitrary than the current algorithm:
    adding random digits to the end of the keyword
    """
    newkey = ""
    for char in key:
        if char in string.ascii_letters:
            newkey += char
        elif char in string.digits:
            newkey += char

    others = model.objects.filter(keyword=newkey).all()
    while len(others) > 0:
        newkey += random.choice(string.digits)
        others = model.objects.filter(keyword=newkey).all()
    return newkey


def scrape_list(l):
    """
    scrapes a list like "trumpet, trombone, accordian" into ->
    ["trumpet","trombone","accordian"] """
    return [elt.strip() for elt in l.split(",") if elt.strip() != ""]


def get_autocomplete(request):
    """
    these functions are used in ajax calls to populate autocomplete drowdowns
    each one tries to order the entries in a salient way, and sends them to
    their respective ajax calls. See feeds.js and jamnow.js
    """

    from accounts.models import Genre, Instrument, Location

    def get_sorted_genres():
        genres = Genre.objects.annotate(count=Count("profiles")).order_by("-count")
        return [genre.name for genre in genres]

    def get_sorted_instruments():
        instruments = Instrument.objects.annotate(count=Count("musicians")).order_by(
            "-count"
        )
        return [instrument.name for instrument in instruments]

    def get_sorted_locations():
        from_venue = Q(profiles__organization__venue__isnull=False)
        venue_locs = Location.objects.filter(from_venue)
        other_locs = (
            Location.objects.filter(~from_venue)
            .annotate(count=Count("profiles"))
            .order_by("-count")
        )
        return [loc.most_exact for loc in other_locs] + [
            "Venue: " + loc.most_exact for loc in venue_locs
        ]

    info = json.loads(request.GET["info"])
    response = {}
    if "genres" in info:
        response.update({"genres": get_sorted_genres()})
    if "instruments" in info:
        response.update({"instruments": get_sorted_instruments()})
    if "locations" in info:
        response.update({"locations": get_sorted_locations()})

    return JsonResponse(response)


def get_objects_near(model, objects, location):
    """
    does what it sounds like, returns a queryset of profiles near the given
    location (string) uses +-.1 lat/lng to judge if something is "near"
    gets called in feeds / jam now filtering (views.py)
    """
    g = geocoders.GoogleV3()
    try:
        geoed_location, (lat, lng) = list(g.geocode(location, exactly_one=False))[0]
        return (
            objects.filter(location__lat__gte=lat - 0.1)
            .filter(location__lat__lte=lat + 0.1)
            .filter(location__lng__gte=lng - 0.1)
            .filter(location__lng__lte=lng + 0.1)
        )
    except:
        return model.objects.none()


def _render_template_node(template, context, name):
    if type(template) == NodeList:
        nodelist = template
    else:
        nodelist = template.template.nodelist
    for node in nodelist:
        if isinstance(node, BlockNode) and node.name == name:
            return node.render(Context(context))
        elif isinstance(node, ExtendsNode):
            return _render_template_node(node.nodelist, context, name)
    return None


def _update_default_context(context):
    context.update(
        {
            "BASE_URL": settings.BASE_URL,
            "TWITTER_HANDLE": settings.TWITTER_HANDLE,
            "FACEBOOK_HANDLE": settings.FACEBOOK_HANDLE,
            "MEDIUM_HANDLE": settings.MEDIUM_HANDLE,
        }
    )


def render_appropriately(
    request,
    template,
    context,
    metadata=None,
    base="base.html",
    ajax_base="ajax_base.html",
):
    "Based on the request parameter ajax being passed, render as json or html"
    if metadata is None:
        metadata = {}
    try:
        browser = get_browser(request.META["HTTP_USER_AGENT"])
    except KeyError:
        browser = ""

    _update_default_context(context)

    try:
        context["view"] = request.user.person.view
    except:
        pass

    if (
        request.GET.get("ajax", "false") == "true"
        or request.POST.get("ajax", "false") == "true"
    ):
        context["base"] = ajax_base
        context["SERVER"] = settings.SERVER
        j = {
            "content": template.render(context, request),
            "meta": metadata,
            "session_info": get_session_info(request),
        }

        j["title"] = _render_template_node(template, context, "title")

        if "contentclass" in context:
            j["contentclass"] = context["contentclass"]
        if "pageclass" in context:
            j["pageclass"] = context["pageclass"]

        return JsonResponse(j, safe=False)
    else:
        if request.GET:
            context["next"] = request.GET.get("next")

        context["base"] = base
        context["browser"] = browser
        context["SERVER"] = settings.SERVER
        return HttpResponse(template.render(context, request))


def JSON(obj):
    "JSON : python object => HttpRespons( JSON )"
    # Depreciated: This is done for backwards compatibility
    # we swtiched to JsonResponse since an HttpResponse loses the current session
    return JsonResponse(obj, safe=False)
    # return JsonResponse(json.dumps(obj, separators=(',', ':')), safe=False)
    # return HttpResponse(json.dumps(obj, separators=(',', ':')),
    #                     content_type='application/javascript')


def pretty_money(amount):
    """
    pretty_money: some number mon.eylksf => "$mon.ey"
    represents a number as dollars and cents
    """
    return "$%.2f" % round(float(amount), 2)


def get_browser(ua):
    # A really rudamentary browser check given a
    # request.meta['HTTP_USER_AGENT']
    if "Chrome" in ua:
        return "chrome"
    elif "Safari" in ua:
        return "safari"
    elif "Firefox" in ua:
        return "firefox"
    elif "MSIE" in ua:
        return "msie"
    elif "Opera" in ua:
        return "opera"
    else:
        return None


def base64url(img, fmt=None):
    "base64url : PIL Image -> base64 css value for background or source"
    if fmt:
        fmt = {"JPEG": "jpeg", "PNG": "png"}[fmt]
    else:
        fmt = {"JPEG": "jpeg", "PNG": "png"}[img.format()]
    return "url(data:image/%s;base64,%s);" % (
        fmt,
        base64.b64encode(img).decode("utf-8"),
    )


def ensure_valid_JSON(json):
    """
    Takes a JSON string and makes sure there are quotes around the keys,
    so json.loads doesn't bitch about it. Basically, not all JavaScript-valid
    JSON, when stringified, makes json.loads happy. Run this on on the
    stringified version to make sure json.loads likes it.

    Thank you cheeseinvert and Ned Batchelder
    http://stackoverflow.com/a/9184162/827559
    """

    json = re.sub(r"{\s*'?(\w)", r'{"\1', json)
    json = re.sub(r",\s*'?(\w)", r',"\1', json)
    json = re.sub(r"(\w)'?\s*:", r'\1":', json)
    json = re.sub(r":\s*'(\w*)'\s*([,}])", r':"\1"\2', json)
    return json


def flipstr(s, a, b):
    return str(s).replace(a, "REPLACETHIS").replace(b, a).replace("REPLACETHIS", b)


def add_raw_reviews(feed):
    # Note: Not currently used
    # Manually get profiles of items since the generic relation selection is
    # too expensive
    from django.db import connection

    cursor = connection.cursor()

    # Store the content types, object id's, and feed id's to use in raw query
    ctype_ids = []
    obj_ids = []
    feed_id_list = []
    for ff in feed:
        ctype_ids.append(ff.content_type_id)
        obj_ids.append(ff.object_id)
        feed_id_list.append(ff.id)
    ctype_ids = tuple(set(ctype_ids))
    obj_ids = tuple(set(obj_ids))
    feed_id_list = tuple(set(feed_id_list))

    # Get the tables we need
    tables = []
    for cid in ctype_ids:
        cursor.execute("SELECT * FROM django_content_type " "WHERE id = %s", [cid])
        row = cursor.fetchone()
        tables.append(row[2] + "_" + row[3])

    raw_review_targets = {}
    raw_review_text = {}
    for tbl in tables:
        # Only accounts_review is supported for now
        if tbl == "accounts_review":
            # Raw query to get the feed items
            q = """
SELECT DISTINCT
    activity_feed.id,
    {0!s}.profile.keyword,
    {0!s}.profile.name,
    {0!s}.review FROM {0!s}
INNER JOIN accounts_profile AS profile
    ON {0!s}.profile_id = profile.id
LEFT JOIN activity_feed
WHERE
    activity_feed.id IN {1!s} AND
    {0!s}.id IN {2} AND
    activity_feed.from_profile_id={0!s}.reviewer_id AND
    activity_feed.to_profile_id={0!s}.profile_id
ORDER BY activity_feed.created_at DESC
            """.format(
                tbl, feed_id_list, obj_ids
            )
            cursor.execute(q)
            row = cursor.fetchall()

            # Construct the review_target links and save the review text
            for r in row:
                raw_review_targets[
                    r[0]
                ] = "<a class='profile-ajax' href='/profile/{}'>{}</a>".format(
                    r[1], r[2]
                )
                raw_review_text[r[0]] = r[3]

            # Add them to Feed instances
            for ff in feed:
                if ff.id in raw_review_targets:
                    ff.raw_review_target = raw_review_targets[ff.id]
                    ff.raw_review_text = raw_review_text[ff.id]

    return feed


class OrderedSet(collections.OrderedDict, collections.MutableSet):
    def update(self, *args, **kwargs):
        if kwargs:
            raise TypeError("update() takes no keyword arguments")

        for s in args:
            for e in s:
                self.add(e)

    def add(self, elem):
        self[elem] = None

    def discard(self, elem):
        self.pop(elem, None)

    def __le__(self, other):
        return all(e in other for e in self)

    def __lt__(self, other):
        return self <= other and self != other

    def __ge__(self, other):
        return all(e in self for e in other)

    def __gt__(self, other):
        return self >= other and self != other

    def __repr__(self):
        return "OrderedSet([%s])" % (", ".join(map(repr, list(self.keys()))))

    def __str__(self):
        return "{%s}" % (", ".join(map(repr, list(self.keys()))))

    difference = property(lambda self: self.__sub__)
    difference_update = property(lambda self: self.__isub__)
    intersection = property(lambda self: self.__and__)
    intersection_update = property(lambda self: self.__iand__)
    issubset = property(lambda self: self.__le__)
    issuperset = property(lambda self: self.__ge__)
    symmetric_difference = property(lambda self: self.__xor__)
    symmetric_difference_update = property(lambda self: self.__ixor__)
    union = property(lambda self: self.__or__)
