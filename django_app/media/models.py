import logging
import os
import re
import datetime
from functools import reduce

from PIL import Image

from django.conf import settings
from django.db import models
from django.template import loader
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum

import ranking
import utils
from tartar import CallMeMaybe
from infrared import Context

from . import DownloadType
from . import managers


DEF_MUSICLISTING_IMG = "public/images/default-music-listing.svg"

logger = logging.getLogger(__name__)


class Listen(models.Model):
    user = models.ForeignKey(User, related_name="listens", on_delete=models.CASCADE)
    song = models.ForeignKey(
        "media.Song", related_name="listens", on_delete=models.CASCADE
    )
    seconds = models.PositiveIntegerField(null=False)
    datetime = models.DateTimeField(auto_now_add=True, null=True)
    datetime_processed = models.DateTimeField(null=True)
    free = models.BooleanField(default=False)

    def __str__(self):
        return "{} - {} ({})".format(
            self.user.email, self.song.title, self.song.profile.name
        )

    class Meta:
        get_latest_by = "datetime"


class Video(models.Model):
    profile = models.ForeignKey(
        "accounts.Profile", related_name="videos", on_delete=models.CASCADE
    )
    embed_id = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    upload_date = models.DateField(auto_now_add=True, null=True)

    class Meta:
        get_latest_by = "upload_date"


class Photo(models.Model):
    profile = models.ForeignKey("accounts.Profile", on_delete=models.CASCADE)
    upload_date = models.DateField(auto_now_add=True, null=True)
    full_file = models.ImageField(upload_to="images/full")
    thumbnail_file = models.ImageField(
        upload_to="images/thumbnails", blank=True, null=True
    )
    square_file = models.ImageField(upload_to="images/squares", blank=True, null=True)
    profile_file = models.ImageField(
        upload_to="images/profile_file", blank=True, null=True
    )
    crop_top = models.PositiveIntegerField(blank=True, null=True)
    crop_bottom = models.PositiveIntegerField(blank=True, null=True)
    crop_left = models.PositiveIntegerField(blank=True, null=True)
    crop_right = models.PositiveIntegerField(blank=True, null=True)
    caption = models.CharField(max_length=200, blank=True, null=True)

    processing = models.BooleanField(default=False)
    is_banner = models.BooleanField(default=False)
    is_cover = models.BooleanField(default=False)

    class Meta:
        get_latest_by = "upload_date"

    def __str__(self):
        return self.full_file.name

    def is_primary(self):
        return self.profile.primary_photo == self

    def jsonify(self, request):
        j = {
            "id": self.pk,
            "name": self.full_file.path,
            "full_file": str(self.full_file),
            "square_file": str(self.square_file),
            "full_file_width": str(self.full_file.width),
            "full_file_height": str(self.full_file.height),
            "path": "/" + str(self.profile_file),
            "prof_width": str(self.profile_file.width),
            "prof_height": str(self.profile_file.height),
        }
        return j


class Banner(models.Model):
    photo = models.OneToOneField(
        Photo, related_name="banner", blank=True, null=True, on_delete=models.CASCADE
    )
    profile = models.OneToOneField(
        "accounts.Profile",
        related_name="banner",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    texture = models.ImageField(upload_to="images/textures", blank=True, null=True)
    texture_resized = models.ImageField(
        upload_to="images/textures_resized", blank=True, null=True
    )
    texture_cropped = models.ImageField(
        upload_to="images/textures_cropped", blank=True, null=True
    )
    texture_chosen = models.CharField(max_length=15, blank=True, null=True)
    crop_top = models.PositiveIntegerField(blank=True, null=True)
    crop_bottom = models.PositiveIntegerField(blank=True, null=True)
    crop_left = models.PositiveIntegerField(blank=True, null=True)
    crop_right = models.PositiveIntegerField(blank=True, null=True)
    font = models.CharField(max_length=100, blank=True, null=True)
    display_title = models.BooleanField(default=True)
    display_genre = models.BooleanField(default=True)
    display_instrument = models.BooleanField(default=True)
    display_location = models.BooleanField(default=True)
    display_bar = models.BooleanField(default=False)
    texture_temp = models.ImageField(
        upload_to="images/textures_temp", blank=True, null=True
    )
    texture_temp_resized = models.ImageField(
        upload_to="images/textures_temp", blank=True, null=True
    )

    def cropped_path(self):
        # Returns usable url for the main cropped source
        path = self.texture_cropped.path
        return "/%s" % path[path.index("images/") :]

    def preview_tile(self):
        try:
            # Returns base64 of picture for preview in Dashboard (to simulate
            # tiling)
            cropped = Image.open(self.texture_cropped)
            fmt = cropped.format
            width, height = cropped.size
            # Width to height ratio
            ratio = float(width) / float(height)
            new_width = float(width) * 0.527
            cropped = cropped.resize(
                (int(new_width), int(new_width / ratio)), Image.ANTIALIAS
            )

            cropped.save("%s_tmp" % self.profile.keyword, fmt)
            f = open("%s_tmp" % self.profile.keyword, "rb")
            data = f.read()
            f.close()
            os.remove("%s_tmp" % self.profile.keyword)
            return utils.base64url(data, fmt)
        except (ValueError, FileNotFoundError):
            # No banner uploaded yet
            return "rgba(0,0,0,0.1)"


class Radio(models.Model):
    profile = models.OneToOneField(
        "accounts.Profile", related_name="radio", on_delete=models.CASCADE
    )

    def jsonify(self, request):
        prof = self.profile.jsonify(request.user.profile)
        return {
            "id": self.pk,
            "profile": prof,
            "type": "radio",
        }


class MusicUpload(models.Model):
    profile = models.ForeignKey(
        "accounts.Profile", related_name="music", on_delete=models.CASCADE
    )
    upload_date = models.DateField(auto_now_add=True, null=True)
    fans = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    splash_featured = models.BooleanField(default=False)

    """
    download_type: str

    One of the following:
    'normal'
    'none'
    'name_price'
    'free'

    """
    download_type = models.CharField(max_length=10, choices=DownloadType.CHOICES)

    price = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    portion_donated = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True
    )

    # unique keyword for every upload
    # max length increased to 255 to account for long file names

    keyword = models.SlugField(max_length=255)

    # dont actually delete the songs
    deleted = models.BooleanField(default=False)

    # cached rankings for each music upload (for music page)
    rank_all = models.IntegerField(default=0)
    rank_today = models.IntegerField(default=0)
    rank_week = models.IntegerField(default=0)
    rank_month = models.IntegerField(default=0)
    rank_year = models.IntegerField(default=0)

    # true if we verify it and it's in the echonest database
    # we can set suspicious = false when we get confirmation
    # can also use this for albums in the future
    suspicious = models.BooleanField(default=False)

    class Meta:
        get_latest_by = "upload_date"

    def get_absolute_url(self):
        """Since media uploads dont currently support linking we link to the
        profile"""
        return "/profile/%s" % self.profile.keyword

    def online(self):
        return False

    def save(self, *args, **kwargs):
        to_update = kwargs.pop("update", False)
        super().save(*args, **kwargs)
        if to_update:
            ranking.update(self)

    def avg_review_rating(self):
        stars = [
            r.stars for r in self.get_reviews().filter(stars__gt=0)  # type: ignore
        ]
        if len(stars) > 0:
            return float(float(sum(stars)) / len(stars))
        else:
            return 0

    def get_pretty_price(self):
        if self.download_type == "none":
            return "N/A"
        elif self.download_type == "normal":
            return "$" + ("%.*f" % (2, self.price)) if self.price > 0 else "Free"
        elif self.download_type == "name_price":
            return "NYP"
        elif self.download_type == "free":
            return "Free"
        else:
            return ""

    def get_price_string(self):
        # Why y'all coding bugs into this and not testing?
        if self.download_type == "normal" or self.download_type == "name_price":
            # always return 2 decimal places
            return "%.*f" % (2, self.price)
        elif self.download_type == "free":
            return "Free"
        elif self.download_type == "none":
            return "Stream Only"
        else:
            return False

    def get_pretty_download_type(self):
        return dict(DownloadType.CHOICES).get(self.download_type, "Stream Only")

    def fanned(self, request):
        raise NotImplementedError("Needs to be implemented in sub-class")

    def owned(self, request):
        raise NotImplementedError("Needs to be implemented in sub-class")

    def jsonify(self, request):
        return {
            "artist": self.profile.jsonify(request),
            "artistName": self.profile.name,
            "priceVal": float(self.price),
            "price": self.get_price_string(),
            "fanned": self.fanned(request),
            "owned": self.owned(request),
            "pretty_price": self.get_pretty_price(),
            "download_type": self.download_type,
            "pretty_download_type": self.get_pretty_download_type(),
            "artistKeyword": self.profile.keyword,
            "forSale": "no" if self.download_type == "none" else "yes",
        }

    def get_name(self):
        try:
            return self.media_album.title  # type: ignore
        except:
            return self.media_song.title  # type: ignore

    def __str__(self):
        return self.get_name()


class Album(MusicUpload):
    title = models.CharField(max_length=100)
    cover = models.OneToOneField(
        "Photo", related_name="album", null=True, on_delete=models.CASCADE
    )

    full_cover = models.ImageField(upload_to="images/full_album", null=True, blank=True)
    medium_cover = models.ImageField(
        upload_to="images/medium_album", null=True, blank=True
    )
    small_cover = models.ImageField(
        upload_to="images/small_album", null=True, blank=True
    )

    year_released = models.PositiveIntegerField(blank=True, null=True)
    musicupload_ptr = models.OneToOneField(
        MusicUpload,
        related_name="media_album",
        on_delete=models.CASCADE,
        parent_link=True,
    )
    available = models.BooleanField(default=False)
    # updates the albums availablity (able to stream)

    # DEPRECATED
    album_cover = models.ImageField(upload_to="images/full", null=True, blank=True)

    objects = managers.AlbumQuerySet.as_manager()

    def is_available(self):
        if self.songs.count():  # type: ignore
            self.available = reduce(
                lambda x, y: x and y,
                [
                    s.available() for s in self.songs.all()  # type: ignore
                ],
            )
        else:
            self.available = False
        return self.available

    def save(self, *args, **kwargs):
        self.is_available()
        super().save(*args, **kwargs)

    def hottness(self, after_date):
        # album hottness is based on the total for its songs
        if self.songs.count() == 0:  # type: ignore
            return 0
        score = self.get_fans_after(after_date).count()
        if self.splash_featured:
            score += settings.SPLASH_FEATURED_ALBUM_HOTTNESS_VALUE
        score += sum([song.hottness(after_date) for song in self.get_songs()]) / (
            self.songs.count() + 1  # type: ignore
        )
        return score

    def get_artwork(self):
        return self.medium_cover or self.profile.primary_photo or DEF_MUSICLISTING_IMG

    def full(self):
        return (
            "/" + str(self.full_cover)
            if self.full_cover
            else "/public/images/default-music-listing.svg"
        )

    def medium(self):
        return (
            "/" + str(self.medium_cover)
            if self.medium_cover
            else "/public/images/default-music-listing.svg"
        )

    def small(self):
        return (
            "/" + str(self.small_cover)
            if self.small_cover
            else "/public/images/default-music-listing.svg"
        )

    def fanned(self, request):
        from accounts.models import AlbumFanEvent

        fanned = False
        if request and request.user.is_authenticated:
            profile = request.user.person.view
            fanned = AlbumFanEvent.objects.filter(
                faned_album=self, faner=profile
            ).exists()
        return fanned

    def owned(self, request):
        from accounts.models import MediaDownload

        owned = False
        if request and request.user.is_authenticated:
            profile = request.user.person.view
            owned = MediaDownload.objects.filter(
                media=self, charge__profile=profile
            ).exists()
        return owned

    def jsonify(self, request):
        from accounts.models import Review

        ret = {
            "artist": self.profile.jsonify(request),
            "id": self.pk,
            "title": self.title,
            "full_cover": self.full(),
            "medium_cover": self.medium(),
            "small_cover": self.small(),
            "year_released": self.year_released,
            "songs": [s.jsonify(request) for s in self.get_online_songs()],
            "reviews_count": len(Review.objects.filter(album=self)),
            "type": "album",
        }
        ret.update(MusicUpload.jsonify(self, request))
        return ret

    def as_music_listing(self, request):
        return loader.render_to_string(
            "common/music.listing.html",
            {
                "title": self.title,
                "subtitle": "by %s" % self.profile.name,
                "image": self.small_cover or DEF_MUSICLISTING_IMG,
                "profileurl": self.profile.get_absolute_url(),
                "entity_type": "album",
                "play_button_type": "album",
                "play_button_id": self.pk,
                "entity": self,
                "view": utils.get_profile(request.user),
            },
        )

    def get_online_songs(self, online_only=True):
        "Online songs by tracknum"
        return self.songs.filter(deleted=False, online=True, processing=False).order_by(  # type: ignore
            "track_num"
        )

    def get_songs(self):
        "Get all songs ordered by tracknum"
        return self.songs.filter(deleted=False).order_by("track_num")  # type: ignore

    def add_fan(self, profile):
        from accounts.models import AlbumFanEvent

        # make sure you're not already a fan
        if not AlbumFanEvent.objects.all().filter(faned_album=self, faner=profile):
            self.fans += 1
            faned = AlbumFanEvent.objects.create(faned_album=self, faner=profile)
            self.save(update=True)

            return faned
        return None

    def remove_fan(self, profile):
        from accounts.models import AlbumFanEvent

        # make sure you're a fan
        if AlbumFanEvent.objects.all().filter(faned_album=self, faner=profile):
            self.fans -= 1  # type: ignore
            AlbumFanEvent.objects.get(faned_album=self, faner=profile).delete()

            self.save(update=True)

            return ",'>)"
        return None

    def __str__(self):
        return self.title

    def get_reviews(self):
        from accounts.models import Review

        return Review.objects.filter(album=self)

    def get_fans_after(self, after_date):
        from accounts.models import AlbumFanEvent

        if after_date:
            return AlbumFanEvent.objects.filter(
                faned_album=self, faned_date__gte=after_date
            )
        else:
            return AlbumFanEvent.objects.filter(faned_album=self)

    def get_fan_number(self):
        return self.get_fans().length  # type: ignore

    def get_shortened_title(self):
        if len(self.title) < 30:
            return self.title
        return self.title[:30] + "..."

    def get_elapsed_length(self):
        q = self.songs.filter(visible=True, online=True, deleted=False)  # type: ignore
        s = sum([s.length for s in q.filter(length__isnull=False)])
        num_songs_with_no_length_set = q.filter(length__isnull=True).count()
        approx = ""
        if num_songs_with_no_length_set:
            approx = "approx "
            s += num_songs_with_no_length_set * 4
        minutes = str(s % 60)
        if len(minutes) == 1:
            minutes += "0"
        return "{}{}:{}".format(approx, s / 60, minutes)

    def get_cover(self):
        "Used to get cover for downloads"
        return self.full_cover or self.profile.get_music_listing_img()


class Song(MusicUpload):
    album = models.ForeignKey(
        "Album", null=True, blank=True, related_name="songs", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="", null=True)
    processing = models.BooleanField(default=False)
    online = models.BooleanField(default=False)  # type: ignore
    visible = models.BooleanField(default=False)  # Not really used

    title = models.CharField(max_length=100)
    track_num = models.PositiveSmallIntegerField(blank=True, null=True)
    length = models.PositiveIntegerField(blank=True, null=True)
    musicupload_ptr = models.OneToOneField(
        MusicUpload,
        related_name="media_song",
        parent_link=True,
        on_delete=models.CASCADE,
    )

    state_info = models.CharField(max_length=1000, null=True)

    # International Standard Recording Code
    isrc = models.CharField(max_length=12, null=True, blank=True)

    # EAN (European Article Numbers also called International Article Numbers)
    # The EAN contains a 13 digit number
    # UPC (Universal Product Codes)
    # UPC contains a 12 digit number.
    upc_ean = models.CharField(max_length=12, null=True, blank=True)

    objects = managers.SongQuerySet.as_manager()

    class Meta:
        ordering = ("album", "track_num")

    def get_absolute_url(self):
        """Since media uploads dont currently support linking we link to the
        profile"""
        return "/song/{}".format(self.keyword)

    def available(self):
        return not self.processing and not self.deleted and self.visible and self.online

    def getlength(self):
        cmm = CallMeMaybe(Context(settings.CONFIG))
        return cmm.getlength(self.pk, CallMeMaybe.Song)

    def streaming_url(self):
        cmm = CallMeMaybe(Context(settings.CONFIG))
        url = cmm.getpublicurl(self.pk, CallMeMaybe.Song)
        if url:
            # type: ignore
            reg = re.search(
                "^(?P<http>http|https):\/\/(?P<prefix>[a-zA-Z0-9-]*).*\/(?P<suffix>.*)",
                url,
            )
            if reg is not None:
                parts = reg.groupdict()
                if parts["http"] == "http":
                    # If the url is not https, likely rackspace api returned a url
                    # which was stored in rethinkdb that no longer works, hence the
                    # need to fix the url.
                    # If this breaks in the future, likely rackspace changed their api
                    # url scheme again

                    # Prefix is always the same at the moment however
                    return "https://{prefix}.ssl.cf1.rackcdn.com/{suffix}".format(
                        **parts
                    )
                # If keyword is not set, we can set it now
                # (Keyword may not have been set due to a previous bug)
                if not self.keyword:
                    self.keyword = parts["suffix"].split(".")[0]
                    self.save()
        return url

    def get_artwork(self):
        # Is it on an album?
        if self.album and self.album.medium_cover:
            return "/%s" % self.album.medium_cover.url
        elif self.profile.primary_photo:
            return "/%s" % self.profile.primary_photo.square_file.url
        else:
            return "/%s" % DEF_MUSICLISTING_IMG

    def fanned(self, request):
        from accounts.models import SongFanEvent

        fanned = False
        if request and request.user.is_authenticated:
            profile = request.user.person.view
            fanned = SongFanEvent.objects.filter(
                faned_song=self, faner=profile
            ).exists()
        return fanned

    def owned(self, request):
        from accounts.models import MediaDownload

        owned = False
        if request and request.user.is_authenticated:
            profile = request.user.person.view
            owned = MediaDownload.objects.filter(
                media=self, charge__profile=profile
            ).exists()
        return owned

    def jsonify(self, request):
        ret = {
            "id": self.pk,
            "title": self.title,
            "short_title": self.get_shortened_title(),
            "duration": self.get_formatted_length(),
            "reviews_count": len(self.get_reviews()),
            "length": int(self.length) if self.length else "",
            "path": self.streaming_url(),
            "type": "song",
            "artwork": self.get_artwork(),
            "as_admin_listing": loader.render_to_string(
                "common/songlisting_div.html",
                {
                    "song": self,
                    "view": request.user.person.view
                    if request and request.user.is_authenticated
                    else None,
                    "admin": True,
                },
            ),
        }
        ret.update(MusicUpload.jsonify(self, request))
        return ret

    def as_music_listing(self, request):
        return loader.render_to_string(
            "common/music.listing.html",
            {
                "title": self.title,
                "subtitle": "by %s" % self.profile.name,
                "image": self.get_music_listing_img() or DEF_MUSICLISTING_IMG,
                "profileurl": self.profile.get_absolute_url(),
                "entity_type": "song",
                "play_button_type": "song",
                "play_button_id": self.pk,
                "entity": self,
                "view": utils.get_profile(request.user),
            },
        )

    def hottness(self, after_date):
        if after_date:
            score = self.plays.filter(timestamp__gte=after_date).count()  # type: ignore
        else:
            score = self.plays.count()  # type: ignore

        listens = (
            Listen.objects.values("song")
            .annotate(total_seconds=Sum("seconds"))
            .filter(song=self)
        )
        if after_date:
            listens = listens.filter(datetime_processed__gte=after_date)

        if listens:
            # average song length is 3 minutes so to equate it with
            # a 'play' we divide by 180
            score_listens = listens[0]["total_seconds"] / 180
            logger.debug(
                "score_listens=%s (%ss)", score_listens, listens[0]["total_seconds"]
            )
            score += score_listens

        # if a song is featured, we give it a plus 100
        # giving a song a large hotness value will likely get the
        # artist and album featured as well, so better to
        # put splash_featured for artists than individual songs
        # or significantly reduce the values spash value here
        if self.splash_featured:
            score_splash = settings.SPLASH_FEATURED_SONG_HOTTNESS_VALUE
            logger.debug("score_splash=%s", score_splash)
            score += score_splash

        score_purchases = float(sum(self.get_all_purchase_prices(after_date)))
        logger.debug("score_purchases=%s", score_purchases)
        score += score_purchases

        score_fans = self.get_fans_after(after_date).count()
        logger.debug("score_fans=%s", score_fans)
        score += score_fans

        return score

    def get_reviews(self):
        from accounts.models import Review

        return Review.objects.filter(song=self)

    def get_shortened_title(self):
        if len(self.title) < 30:
            return self.title
        return self.title[:30] + "..."

    def add_fan(self, profile):
        "make sure you're not already a fan"
        from accounts.models import SongFanEvent

        if not SongFanEvent.objects.all().filter(faned_song=self, faner=profile):
            self.fans += 1
            SongFanEvent.objects.create(faned_song=self, faner=profile)
            self.save(update=True)

            return "success"
        return None

    def remove_fan(self, profile):
        "make sure you're a fan"
        from accounts.models import SongFanEvent

        if SongFanEvent.objects.all().filter(faned_song=self, faner=profile):
            self.fans -= 1  # type: ignore
            SongFanEvent.objects.get(faned_song=self, faner=profile).delete()
            self.save(update=True)
            return ",'>)"
        return None

    def get_formatted_length(self):
        "Seconds to h:m:s"
        if self.length:
            return str(datetime.timedelta(seconds=self.length))
        return ""

    def get_fans_after(self, after_date):
        from accounts.models import SongFanEvent

        if after_date:
            return SongFanEvent.objects.filter(
                faned_song=self, faned_date__gte=after_date
            )
        else:
            return SongFanEvent.objects.filter(faned_song=self)

    def get_all_purchase_prices(self, after_date=None):
        download_objects = self.download_objects.all()  # type: ignore
        if after_date:
            download_objects = download_objects.filter(charge__date__gte=after_date)
        return [1 + d.price for d in download_objects]

    def was_uploaded_to_s3(self):
        "Test if the file was uploaded to S3"
        import boto

        conn = boto.connect_s3(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)
        bucket = conn.get_bucket(settings.S3_BUCKET)
        s3_song = bucket.get_key(self.keyword)
        return bool(s3_song)

    def get_cover(self):
        "Used to get cover for downloads"
        return (
            self.album and self.album.full_cover or self.profile.get_music_listing_img()
        )

    def get_music_listing_img(self):
        "Used to get the mini cover"
        return (
            self.album
            and self.album.small_cover
            or self.profile.get_music_listing_img()
        )

    def __str__(self):
        return self.title
