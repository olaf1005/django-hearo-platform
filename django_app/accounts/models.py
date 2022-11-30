import pgpy
import logging
import string
import random
from decimal import Decimal, ROUND_UP, ROUND_DOWN
import datetime
import requests

import json
from PIL import Image
import geopy
from geopy import distance

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.template import loader
from django.template.defaultfilters import slugify
from django.contrib.postgres.fields import ArrayField, JSONField

from caching.base import CachingManager, CachingMixin

from accounts import DEF_MUSICLISTING_IMG
from activity.models import Feed
from media import DownloadFormat
from media.models import Listen, Song

from worldmap.geography import COUNTRIES
import mail
import ranking
import utils


logger = logging.getLogger(__name__)


class ProfileManager(CachingManager, models.Manager):
    def get_query_set(self):
        return super().get_query_set().filter(deactivated=False)  # type: ignore


class OldManager(CachingManager, models.Manager):
    pass


class Profile(CachingMixin, models.Model):
    objects = ProfileManager()
    all_objects = OldManager()

    # TODO: why is blank and null true?? if we create a profile a user
    # should be present which attaches to that profile
    # if a user leaves a profile, (should) another member/user should be
    # delegated responsibility
    user = models.OneToOneField(
        User, related_name="profile", blank=True, null=True, on_delete=models.CASCADE
    )
    allow_send_receive = models.BooleanField(default=False)
    suspicious = models.BooleanField(default=False)
    # url is '/profile/' + keyword
    deactivated = models.BooleanField(default=False)
    keyword = models.SlugField(max_length=100, null=True, unique=True)
    email_normalized = models.EmailField(null=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50)
    date_added = models.DateField(auto_now_add=True, null=True)
    primary_photo = models.OneToOneField(
        "media.Photo",
        null=True,
        related_name="primary_owner",
        on_delete=models.SET_NULL,
    )
    biography = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        get_latest_by = "date_added"

    # This is a string that we use to save certain profile layout tweaks the
    # user makes in stringified JSON format.
    # Currently there's two settings: updatesHeight and fansHeight, so a
    # profile_layout_setting string might look like this:
    # "{updatesHeight: 352, fansHeight: 412}"
    # These are loaded and applied to the profile whenever someone opens it,
    # and can be adjusted in the UI by the owner of the profile only.
    profile_layout_settings = models.CharField(max_length=500)

    def layout_settings_dict(self):
        # Get the layout settings as a Python dict
        return json.loads(self.profile_layout_settings)

    def commit_layout_settings_from_dict(self, usersettings):
        # Given a dict, parse it into a JSON string and save it.
        self.profile_layout_settings = utils.ensure_valid_JSON(json.dumps(usersettings))
        self.save()
        logger.info(self.profile_layout_settings)

    def set_layout_attr(self, attr, height):
        # Given a new value, set layout setting attr to that value
        # Example:
        # p.set_layout_attr("updatesHeight", 315)
        settings_ = self.layout_settings_dict()
        settings_[attr] = height
        self.commit_layout_settings_from_dict(settings_)

    genres = models.ManyToManyField("Genre", blank=True, related_name="profiles")

    influences = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    goals = models.TextField(blank=True, null=True)
    fans = models.ManyToManyField(
        "self", blank=True, through="Fan", symmetrical=False, related_name="fanned"
    )

    location = models.ForeignKey(
        "Location",
        blank=True,
        null=True,
        related_name="profiles",
        on_delete=models.SET_NULL,
    )

    location_set = models.BooleanField(default=False)

    # Set to True to feature this profile on the splash page.
    splash_featured = models.BooleanField(default=False)

    # private data
    p_city = models.CharField(blank=True, max_length=200, null=True)

    p_address1 = models.CharField(blank=True, max_length=200, null=True)
    p_address2 = models.CharField(blank=True, max_length=200, null=True)
    p_state = models.CharField(blank=True, max_length=2, null=True)
    p_zip = models.CharField(blank=True, max_length=10, null=True)
    p_city = models.CharField(blank=True, max_length=200, null=True)
    p_country = models.CharField(blank=True, max_length=60, default="", null=True)

    is_international = models.BooleanField(default=True)

    signed_artist_agreement = models.BooleanField(default=False)

    signed_new_artist_agreement = models.BooleanField(default=False)
    signed_new_tc_aggreement = models.BooleanField(default=False)

    down_to_jam = models.BooleanField(default=False)
    on_air = models.BooleanField(default=False)

    credit = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    fanmail_private = models.BooleanField(default=False)
    downloads_private = models.BooleanField(default=False)
    profile_private = models.BooleanField(default=False)

    default_download_format = models.CharField(
        max_length=7, choices=DownloadFormat.CHOICES
    )

    # cached rankings for each person (for music page)
    rank_all = models.IntegerField(default=0)
    rank_today = models.IntegerField(default=0)
    rank_week = models.IntegerField(default=0)
    rank_month = models.IntegerField(default=0)
    rank_year = models.IntegerField(default=0)

    # for directory, measure of how complete your profile is
    rank_dir = models.IntegerField(default=0)

    # settings model, added to store email notification settings
    settings = models.OneToOneField("Settings", null=True, on_delete=models.SET_NULL)

    def first_name(self):
        if self.is_orgo():
            return self.name
        return self.user.first_name

    def last_name(self):
        if self.is_orgo():
            return ""
        return self.user.last_name

    def update_dir_rank(self):
        from media.models import Photo, Video

        songs = self.get_uploaded_songs()

        # Start count
        score = 0

        # Heaviest credit for song plays
        # for song in songs:
        #    score += (song.plays.count() * 3)

        # Credit for song uploads
        score += songs.count() * 2
        score += Photo.objects.filter(profile=self).count()
        score += Video.objects.filter(profile=self).count()

        # Not really that important/easy to spam
        score += StatusUpdate.objects.filter(profile=self).count()

        # Credit for bio; quality profile
        if self.location_set:
            score += 2
        if self.biography:
            score += 2
        if self.influences:
            score += 2
        if self.goals:
            score += 2
        self.rank_dir = score
        self.save()

    def deactivate(self):
        from media.models import MusicUpload

        self.deactivated = True
        self.keyword = None
        # remove profile picture
        self.primary_photo = None
        # deactivate all songs and albums
        for obj in MusicUpload.objects.filter(profile=self):
            obj.deleted = True
            obj.save()
        # delete all fannings
        for fan in Fan.objects.filter(faner=self):
            fan.delete()
        for fan in Fan.objects.filter(fanee=self):
            fan.delete()

        # CASE 1: profile is a person
        if self.is_person():
            person = self.person
            user = self.user
            # get rid of all group membership
            Membership.objects.filter(person=person).delete()
            # free up email so it can be used again
            user = self.user
            # use a random new username because they have to be distinct
            # must be 30 chars
            new = str(datetime.datetime.now()) + "".join(
                [random.choice(string.ascii_letters) for i in range(4)]
            )
            user.email = user.username = new
            user.save()

        # CASE 2: profile is a group
        elif self.is_orgo():
            orgo = self.organization  # type: ignore
            # remove all memberships
            orgo.members.clear()

        self.save()

    # this is pretty terrible. I would just consolidate this into a
    # date_created field in the Profile model
    def age(self):
        today = datetime.datetime.now()
        p = self.person
        if p:
            age = today - p.user.date_joined
        else:
            if self.organization.is_band:  # type: ignore
                age = today - datetime.datetime.combine(
                    self.organization.band.formed_date, datetime.time()  # type: ignore
                )
            else:
                return 0
        # just to make things a little easier when called from hottness
        return age.days + 1

    def get_badges(self):
        badges = []
        if self.organization.is_band:  # type: ignore
            badges.append(("Formed %s" % self.organization.band.formed_date, "formed"))  # type: ignore
            badges.append(("Band", "bands"))
        if self.organization.is_venue:  # type: ignore
            badges.append(("Venue", "venues"))
        if self.organization.is_label:  # type: ignore
            badges.append(("Label", "labels"))

        person = self.person

        if person:
            if person.producer:
                badges.append(("Producer", "producer"))
            if person.is_musician:
                if person.musician.teacher:
                    badges.append(("Teacher", "music-teacher"))
                if person.musician.join_band:
                    badges.append(("Looking to join a band", "join-band"))
                if person.musician.write_music:
                    badges.append(("Song writer", "songwriters"))
            if self.is_artist and person.engineer:
                badges.append(("Sound engineer", "sound engineers"))

        return badges

    def get_reviews(self):
        return Review.objects.filter(profile=self)

    def avg_review_rating(self):
        stars = [r.stars for r in self.get_reviews().filter(stars__gt=0)]
        if len(stars) > 0:
            return float(float(sum(stars)) / len(stars))
        return 0

    def save(self, *args, **kwargs):
        to_update = kwargs.pop("update", False)
        super().save(*args, **kwargs)
        if to_update:
            ranking.update(self)

    def hottness(self, after_date):
        # profile hottness is the sum of all songs / number of songs
        from media.models import Song

        if self.deactivated:
            return 0

        score = self.get_fans_after(after_date).count()
        if self.splash_featured:
            score += settings.SPLASH_FEATURED_ARTIST_HOTTNESS_VALUE
        my_songs = Song.objects.filter(profile=self, deleted=False)
        score += sum([song.hottness(after_date) for song in my_songs]) / (
            my_songs.count() + 1
        )

        return score

    def get_unread(self):
        # Get the unread fanmail for this profile
        return mail.models.Message.objects.filter(to_profile=self, read=False).order_by(  # type: ignore
            "-timestamp"
        )

    def is_person(self):
        try:
            self._person  # type: ignore
        except Person.DoesNotExist:
            return False
        return True

    def is_orgo(self):
        try:
            self.organization  # type: ignore
        except Organization.DoesNotExist:
            return False
        return True

    @property
    def person(self):
        try:
            return self._person  # type: ignore
        except Person.DoesNotExist:
            return None

    def get_mini_thumb(self):
        if self.primary_photo and utils.file_exists(self.primary_photo.thumbnail_file):
            return "/" + str(self.primary_photo.thumbnail_file)
        return "/public/images/defaultUserPhoto_thumb.png"

    def get_thumb(self):
        if self.primary_photo and utils.file_exists(self.primary_photo.thumbnail_file):
            return "/" + str(self.primary_photo.thumbnail_file)
        return "/public/images/default-music-listing.svg"

    def get_square(self):
        if self.primary_photo and utils.file_exists(self.primary_photo.square_file):
            return "/" + str(self.primary_photo.square_file)
        return "/public/images/default-music-listing.svg"

    def get_square_light(self):
        if self.primary_photo and utils.file_exists(self.primary_photo.square_file):
            return "/" + str(self.primary_photo.square_file)
        return "/public/images/defaults/user.thumb.png"

    def primary_dimensions(self):
        if self.primary_photo and utils.file_exists(self.primary_photo.profile_file):
            photo = Image.open(self.primary_photo.profile_file)
            return photo.size
        return None

    def is_primary_landscape(self):
        if self.primary_photo and utils.file_exists(self.primary_photo.profile_file):
            width, height = self.primary_dimensions()  # type: ignore
            return width > height
        return True

    def get_absolute_url(self):
        if self.music.count():  # type: ignore
            return "/profile/%s/music/" % self.keyword
        return "/profile/%s/about/" % self.keyword

    def as_music_listing(self, request):
        return loader.render_to_string(
            "common/music.listing.html",
            {
                "title": self.name,
                "location": self.location,
                "image": self.get_music_listing_img() or DEF_MUSICLISTING_IMG,
                "profileurl": self.get_absolute_url(),
                "entity_type": "artist",
                "play_button_type": "song",
                "play_button_id": self.get_music_listing_songid(),
                "entity": self,
                "view": utils.get_profile(request.user),
                "instrument_genre_string": self.instrument_genre_string(),
            },
        )

    def get_music_listing_img(self):
        if self.primary_photo and utils.file_exists(self.primary_photo.profile_file):
            return self.primary_photo.profile_file
        return None

    def get_music_listing_songid(self):
        songs = self.get_uploaded_songs()
        if len(songs) == 0:
            return None
        # Serve up a random song on Music :)
        # Fun fun fun
        # NOTE: this is a very bad way to select a random song
        return random.choice(songs).id  # type: ignore

    def add_fan(self, profile):
        # make sure you're not already a faned
        if profile == self:
            return None
        if not Fan.objects.all().filter(fanee=self, faner=profile):
            faned = Fan.objects.create(fanee=self, faner=profile)
            self.save()
            return faned
        return None

    def remove_fan(self, profile):
        Fan.objects.filter(fanee=self, faner=profile).delete()
        self.save()

    def get_fans_after(self, after_date):
        if after_date:
            return Fan.objects.filter(fanee=self, faned_date__gte=after_date)
        return Fan.objects.filter(fanee=self)

    def get_fans(self):
        return self.fans.filter(to_fan__fanee=self)

    def get_fan_number(self):
        return self.get_fans().count

    def get_faned(self):
        return Fan.objects.filter(faner=self).select_related("fanee")

    def has_legal_address(self):
        return self.p_address1 != "" and self.p_city != ""

    def get_point(self):
        try:
            return geopy.Point(self.location.lat, self.location.lng)
        except (AttributeError, TypeError):
            return None

    def geo_dist(self, other):
        # 12500 miles == (a little over) half length of equator == farthest
        # possible distance between two points on earth's surface
        # null=True) woah - artur
        self_p = self.get_point()
        other_p = other.get_point()
        return (
            int(distance.distance(self_p, other_p).miles)
            if type(self_p) == geopy.point.Point and type(other_p) == geopy.point.Point  # type: ignore
            else 12500
        )

    def songs_fand(self):
        return SongFanEvent.objects.filter(faner=self)

    def albums_fand(self):
        return AlbumFanEvent.objects.filter(faner=self)

    def is_artist(self):
        from media.models import Song

        # TODO: fix this, this is not a reliable indicator, use account_type
        return Song.objects.filter(profile=self).exists()

    def get_top_song_id(self):
        from media.models import Song

        my_songs = Song.objects.filter(profile=self).order_by("-fans")
        if my_songs.exists():
            return my_songs[0].id
        return -1

    def has_album(self):
        from media.models import Album

        return Album.objects.filter(profile=self).exists()

    def has_song(self):
        from media.models import Song

        return Song.objects.filter(profile=self).exists()

    def get_profile_progress(self):
        # returns a number 1-100 representing how well you've filled out your
        # profile
        progress = 0
        todo = []
        if self.primary_photo:
            progress += 15
        else:
            todo.append(
                {
                    "name": "photo",
                    "description": "Upload a profile picture!",
                    "href": "/my-account/photos",
                }
            )
        if self.location_set:
            progress += 15
        else:
            todo.append(
                {
                    "name": "location",
                    "description": "Set your location, so fans can "
                    "find local music, and artists "
                    "can gather fan data",
                    "href": "/my-account/",
                }
            )

        if self.biography or self.influences or self.experience or self.goals:
            progress += 15
        else:
            todo.append(
                {
                    "name": "about",
                    "description": "Tell us more about yourself!",
                    "href": "/my-account/",
                }
            )
        if self.genres.count() > 0:
            progress += 15
        else:
            todo.append(
                {
                    "name": "genres",
                    "description": "Give us a list of all your genres!",
                    "href": "/my-account/",
                }
            )
        if self.downloads.count() > 0:  # type: ignore
            progress += 15
        else:
            todo.append(
                {
                    "name": "download",
                    "description": "Download your first song!",
                    "href": "/feeds/",
                }
            )

        if (self.is_person() and self.person.is_musician) or (
            self.is_orgo() and self.organization.is_band  # type: ignore
        ):

            if self.has_legal_address() and self.signed_artist_agreement:
                progress += 10
            else:
                todo.append(
                    {
                        "name": "legal",
                        "description": "Give us your legal address and "
                        "sign the artist agreement to start uploading "
                        "music!",
                        "href": "/my-account/legal",
                    }
                )
            if self.is_artist():
                progress += 15
            else:
                todo.append(
                    {
                        "name": "upload",
                        "description": "Upload your first song!",
                        "href": "/my-account/",
                    }
                )
        else:
            progress += 25
        return [progress, todo]

    def get_genre(self):
        try:
            return self.genres.all()[0]
        except:
            return ""

    def get_account_type(self):
        return self.organization.get_type()  # type: ignore

    def get_instruments(self):
        try:
            return ", ".join(
                [
                    ins.name
                    for ins in self._person.musician.instruments.all()  # type: ignore
                ]
            )
        except:
            return ""

    def get_genres(self):
        try:
            return ", ".join([genre.name for genre in self.genres.all()])
        except:
            return ""

    def instrument_genre_string(self):
        try:
            inst = self._person.musician.instruments.all()  # type: ignore
            if inst.count() > 1:
                return ", ".join([x.name for x in inst])
            else:
                genre = self.genres.all()
                return "%s %s" % (genre[0].name, inst[0].name)
        except:
            return ""

    def jsonify(self, request):
        if request and request.user.is_authenticated:
            fand = request.user.person.view in self.fans.all()
        else:
            fand = None

        img_path = "/public/images/default-music-listing.svg"
        if self.primary_photo and utils.file_exists(self.primary_photo.profile_file):
            img_path = "/" + str(self.primary_photo.thumbnail_file)
        sqr_path = "/public/images/default-music-listing.svg"
        if self.primary_photo and utils.file_exists(self.primary_photo.square_file):
            sqr_path = "/" + str(self.primary_photo.square_file)
        json = {
            "img_path": img_path,
            "sqr_path": sqr_path,
            "name": self.name,
            "short_name": self.short_name,
            "keyword": self.keyword,
            "type": "profile",
            "url": self.get_absolute_url(),
            "id": self.id,  # type: ignore
            "dtj": self.down_to_jam,
            "onair": self.on_air,
            "fand": fand,
            "account_type": self.get_account_type(),
            "location": self.location and self.location.most_exact or None,
        }
        try:
            json["instruments"] = [
                ins.name for ins in self._person.musician.instruments.all()  # type: ignore
            ]
        except:
            pass
        return json

    def get_uploaded_songs(self):
        from media.models import Song

        return Song.objects.filter(profile=self, deleted=False, online=True)

    def get_radio_songs(
        self,
        recur=3,
        num_branches=5,
        num_songs=5,
        popularity_sort=0.5,
        traversed=None,
        get_uploaded=False,
    ):
        if traversed is None:
            traversed = []
        # take #num_songs faned songs, then branch into fans and recur down
        # popularity_sort: level of how much to sort by popularity
        songs = [fan.faned_song for fan in self.songs_fand().order_by("?")][:num_songs]
        if get_uploaded:
            songs.extend(self.get_uploaded_songs())
        if recur <= 0:
            return songs

        faned_profiles = (
            self.get_faned()
            .exclude(id__in=traversed)
            .order_by("-faned_date")[:num_branches]
        )
        new_traversed = traversed + [fan.fanee.id for fan in faned_profiles] + [self.id]  # type: ignore
        for fan in faned_profiles:
            p = fan.fanee
            new_num_songs = min(num_songs - 1, 1)
            new_num_branches = min(num_branches, 1)
            to_extend = p.get_radio_songs(
                recur - 1,
                new_num_branches,
                new_num_songs,
                popularity_sort,
                new_traversed,
                True,
            )

            songs.extend(to_extend)

        return songs

    def get_album_song_ids(self):
        from media.models import Album

        ids = []
        for a in Album.objects.filter(profile=self, deleted=False):
            ids += [x.id for x in a.songs.filter(deleted=False)]
        return ids

    def get_non_album_songs(self):
        from media.models import Song

        return Song.objects.filter(profile=self, deleted=False).exclude(
            id__in=self.get_album_song_ids()
        )

    def get_songs_by_album(self):
        from media.models import Album

        songs = {0: self.get_non_album_songs()}
        albums = Album.objects.filter(profile=self)
        for a in albums:
            if a.songs.count() == 0:
                continue
            songs[a.id] = a.songs.filter(deleted=False)
        return songs

    def get_downloads_unpaid(self):
        # returns all downloads not tied to a receipt (and also that link
        # to a charge, for good measure)
        return MediaDownload.objects.filter(
            media__profile=self, receipt__isnull=True, charge__isnull=False
        )

    def num_downloads_unpaid(self):
        return len(self.get_downloads_unpaid())

    def num_users_unpaid(self):
        unique_users_list = []
        downloads = self.get_downloads_unpaid()
        for download in downloads:
            unique_users_list.append(download.charge.profile)
        return len(set(unique_users_list))

    # returns all the receipts of a profile, ordered most to least recent
    def get_receipts(self):
        return self.receipts.order_by("-time_cashed")  # type: ignore

    def get_total_price(self):
        total = 0
        for download in self.get_downloads_unpaid():
            total += download.price
        return utils.pretty_money(total)

    def get_total_stripe_fee(self):
        total = 0
        for download in self.get_downloads_unpaid():
            total += download.stripe_fee()
        return utils.pretty_money(total)

    def get_total_hearo_fee(self):
        total = 0
        for download in self.get_downloads_unpaid():
            total += download.hearo_fee()
        return utils.pretty_money(total)

    def get_total_profit(self):
        return utils.pretty_money(self.get_total_profit_as_float())

    def get_total_profit_as_float(self):
        total = 0
        for download in self.get_downloads_unpaid():
            total += download.profit()
        return total

    # Methods required for generation of digest emails
    def get_fans_last_week(self):
        d = datetime.date.today() - datetime.timedelta(days=7)
        return Fan.objects.filter(fanee=self, faned_date__gte=d).count()

    def get_fans_last_month(self):
        d = datetime.date.today() - datetime.timedelta(days=30)
        return Fan.objects.filter(fanee=self, faned_date__gte=d).count()

    def get_fans_last_year(self):
        d = datetime.date.today() - datetime.timedelta(days=365)
        return Fan.objects.filter(fanee=self, faned_date__gte=d).count()

    def get_songfans_last_week(self):
        from media.models import Song

        d = datetime.date.today() - datetime.timedelta(days=7)
        songs = Song.objects.available().filter(profile=self).values_list("pk")  # type: ignore
        return SongFanEvent.objects.filter(
            faned_song_id__in=songs, faned_date__gte=d
        ).count()

    def get_songfans_last_month(self):
        from media.models import Song

        d = datetime.date.today() - datetime.timedelta(days=30)
        songs = Song.objects.available().filter(profile=self).values_list("pk")  # type: ignore
        return SongFanEvent.objects.filter(
            faned_song_id__in=songs, faned_date__gte=d
        ).count()

    def get_songfans_last_year(self):
        from media.models import Song

        d = datetime.date.today() - datetime.timedelta(days=365)
        songs = Song.objects.available().filter(profile=self).values_list("pk")  # type: ignore
        return SongFanEvent.objects.filter(
            faned_song_id__in=songs, faned_date__gte=d
        ).count()

    def get_albumfans_last_week(self):
        from media.models import Album

        d = datetime.date.today() - datetime.timedelta(days=7)
        albums = Album.objects.available().filter(profile=self).values_list("pk")  # type: ignore
        return AlbumFanEvent.objects.filter(
            faned_album_id__in=albums, faned_date__gte=d
        ).count()

    def get_albumfans_last_month(self):
        from media.models import Album

        d = datetime.date.today() - datetime.timedelta(days=30)
        albums = Album.objects.available().filter(profile=self).values_list("pk")  # type: ignore
        return AlbumFanEvent.objects.filter(
            faned_album_id__in=albums, faned_date__gte=d
        ).count()

    def get_albumfans_last_year(self):
        from media.models import Album

        d = datetime.date.today() - datetime.timedelta(days=365)
        albums = Album.objects.available().filter(profile=self).values_list("pk")  # type: ignore
        return AlbumFanEvent.objects.filter(
            faned_album_id__in=albums, faned_date__gte=d
        ).count()

    def get_total_fan_count(self):
        return self.fans.count()

    def get_songuploads_last_week(self):
        from media.models import Song

        d = datetime.date.today() - datetime.timedelta(days=7)
        return Song.objects.available().filter(profile=self, upload_date__gte=d).count()  # type: ignore

    def get_songuploads_last_month(self):
        from media.models import Song

        d = datetime.date.today() - datetime.timedelta(days=30)
        return Song.objects.available().filter(profile=self, upload_date__gte=d).count()  # type: ignore

    def get_songuploads_last_year(self):
        from media.models import Song

        d = datetime.date.today() - datetime.timedelta(days=365)
        return Song.objects.available().filter(profile=self, upload_date__gte=d).count()  # type: ignore

    def get_albumuploads_last_week(self):
        from media.models import Album

        d = datetime.date.today() - datetime.timedelta(days=7)
        return (
            Album.objects.available().filter(profile=self, upload_date__gte=d).count()  # type: ignore
        )

    def get_albumuploads_last_month(self):
        from media.models import Album

        d = datetime.date.today() - datetime.timedelta(days=30)
        return (
            Album.objects.available().filter(profile=self, upload_date__gte=d).count()  # type: ignore
        )

    def get_albumuploads_last_year(self):
        from media.models import Album

        d = datetime.date.today() - datetime.timedelta(days=365)
        return (
            Album.objects.available().filter(profile=self, upload_date__gte=d).count()  # type: ignore
        )

    def get_library_newsongsfaned_last_week(self):
        d = datetime.date.today() - datetime.timedelta(days=7)
        return SongFanEvent.objects.filter(faner=self, faned_date__gte=d).count()

    def get_library_newsongsfaned_last_month(self):
        d = datetime.date.today() - datetime.timedelta(days=30)
        return SongFanEvent.objects.filter(faner=self, faned_date__gte=d).count()

    def get_library_newsongsfaned_last_year(self):
        d = datetime.date.today() - datetime.timedelta(days=365)
        return SongFanEvent.objects.filter(faner=self, faned_date__gte=d).count()

    def get_library_newalbumsfaned_last_week(self):
        d = datetime.date.today() - datetime.timedelta(days=7)
        return AlbumFanEvent.objects.filter(faner=self, faned_date__gte=d).count()

    def get_library_newalbumsfaned_last_month(self):
        d = datetime.date.today() - datetime.timedelta(days=30)
        return AlbumFanEvent.objects.filter(faner=self, faned_date__gte=d).count()

    def get_library_newalbumsfaned_last_year(self):
        d = datetime.date.today() - datetime.timedelta(days=365)
        return AlbumFanEvent.objects.filter(faner=self, faned_date__gte=d).count()

    def get_library_newprofilesfaned_last_week(self):
        d = datetime.date.today() - datetime.timedelta(days=7)
        return Fan.objects.filter(faner=self, faned_date__gte=d).count()

    def get_library_newprofilesfaned_last_month(self):
        d = datetime.date.today() - datetime.timedelta(days=30)
        return Fan.objects.filter(faner=self, faned_date__gte=d).count()

    def get_library_newprofilesfaned_last_year(self):
        d = datetime.date.today() - datetime.timedelta(days=365)
        return Fan.objects.filter(faner=self, faned_date__gte=d).count()

    def get_downloadcharges_last_week(self):
        d = datetime.date.today() - datetime.timedelta(days=7)
        return MediaDownload.objects.filter(
            receipt__isnull=False, media__profile=self, charge__date__gte=d
        ).count()

    def get_downloadcharges_last_month(self):
        d = datetime.date.today() - datetime.timedelta(days=30)
        return MediaDownload.objects.filter(
            receipt__isnull=False, media__profile=self, charge__date__gte=d
        ).count()

    def get_downloadcharges_last_year(self):
        d = datetime.date.today() - datetime.timedelta(days=365)
        return MediaDownload.objects.filter(
            receipt__isnull=False, media__profile=self, charge__date__gte=d
        ).count()

    def get_downloadcharges_value_last_week(self):
        d = datetime.date.today() - datetime.timedelta(days=7)
        v = MediaDownload.objects.filter(
            receipt__isnull=False, media__profile=self, charge__date__gte=d,
        ).aggregate(Sum("price"))
        return (
            utils.pretty_money(v["price__sum"])
            if v["price__sum"]
            else utils.pretty_money(0)
        )

    def get_downloadcharges_value_last_month(self):
        d = datetime.date.today() - datetime.timedelta(days=30)
        v = MediaDownload.objects.filter(
            receipt__isnull=False, media__profile=self, charge__date__gte=d,
        ).aggregate(Sum("price"))
        return (
            utils.pretty_money(v["price__sum"])
            if v["price__sum"]
            else utils.pretty_money(0)
        )

    def get_downloadcharges_value_last_year(self):
        d = datetime.date.today() - datetime.timedelta(days=365)
        v = MediaDownload.objects.filter(
            receipt__isnull=False, media__profile=self, charge__date__gte=d,
        ).aggregate(Sum("price"))
        return (
            utils.pretty_money(v["price__sum"])
            if v["price__sum"]
            else utils.pretty_money(0)
        )


class Wallet(models.Model):
    user = models.OneToOneField(User, related_name="wallet", on_delete=models.CASCADE)

    openpgp_key = models.TextField(_("OpenPGP Key"), null=False)

    hedera_account_id = models.CharField(
        _("Hedera Account ID"), null=False, max_length=20
    )
    hedera_private_key = models.TextField(_("Hedera Private Key"), null=False)
    hedera_public_key = models.CharField(
        _("Hedera Public Key"), null=False, max_length=100
    )

    token_balance = models.BigIntegerField(default=0)
    token_balance_last_update = models.DateTimeField(null=True, default=None)

    date_added = models.DateField(auto_now_add=True, null=True)

    received_starter_tokens = models.BooleanField(default=False)
    account_associated_with_token = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        get_latest_by = "date_added"

    def get_openpgp_key_object(self):
        key = pgpy.PGPKey()
        key.parse(self.openpgp_key)
        return key

    def unlock_openpgp_key_object(self, password):
        try:
            with self.get_openpgp_key_object().unlock(password) as unlocked:
                return True
        except pgpy.errors.PGPDecryptionError:  # type: ignore
            return False

    def get_encrypted_hedera_private_key_object(self):
        return pgpy.PGPMessage.from_blob(self.hedera_private_key)

    def unlock_hedera_key(self, password):
        priv_key = pgpy.PGPKey()
        priv_key.parse(self.openpgp_key)

        with priv_key.unlock(password) as unlocked_key:
            encrypted_message = pgpy.PGPMessage.from_blob(self.hedera_private_key)
            return unlocked_key.decrypt(encrypted_message).message


class WalletRecovery(models.Model):
    wallet = models.ForeignKey(
        Wallet, related_name="wallet_recovery", on_delete=models.CASCADE
    )
    date_added = models.DateField(auto_now_add=True, null=True)
    # Key re-encrypted using keys of staff members
    encrypted_key = models.TextField(_("Encrypted key"), null=False)
    # Staff members whose keys were used to re-encrypt the key
    recovery_key_hashes = ArrayField(models.CharField(max_length=100))

    def get_encrypted_key_object(self):
        return pgpy.PGPMessage.from_blob(self.encrypted_key)

    class Meta:
        get_latest_by = "date_added"


class HTSTokenTransfer(models.Model):
    from_user = models.ForeignKey(
        User, related_name="user_payments_made", on_delete=models.SET_NULL, null=True
    )
    # Nullable because it can also be sent to a user's wallet
    listen = models.ForeignKey(
        Listen, on_delete=models.SET_NULL, null=True, related_name="tokentransfers"
    )
    # Nullable because it can also be sent to the treasury
    # or to another user
    for_song = models.ForeignKey(
        Song,
        related_name="song_payments_received",
        null=True,
        on_delete=models.SET_NULL,
    )
    from_hedera_account_id = models.CharField(
        _("From Hedera Account ID"), null=True, max_length=20
    )
    memo = models.TextField(_("Memo"), null=True)
    # Value of transfer in JAM
    value = models.BigIntegerField(default=0)
    facilitation_fee = models.BigIntegerField(default=0)
    # Has the token transfer been attempted?
    # e.g. all if all users had a wallet then it would have been attempted
    attempted = models.PositiveIntegerField(default=0)
    datetime = models.DateTimeField(auto_now_add=True, null=True)
    success = models.BooleanField(default=False)
    datetime_success = models.DateTimeField(null=True)
    datetime_last_attempted = models.DateTimeField(null=True)
    retry = models.BooleanField(default=True)

    error = models.CharField(null=True, max_length=300)

    data = JSONField()

    class Meta:
        get_latest_by = "datetime"

    def transfer_token(self, user_private_key=None):
        # NOTE: Some of this code can be refactored into the hedera_utils module
        import hedera_utils

        # Check if account is active or profile has been deactivated (e.g. banned)
        # before proceeding, if the account is reactivated then the transaction will process
        # next time
        # In this case we don't need to consider the flag is suspicious
        # since we want the suspicious user to continue transacting towards the treasury
        if (
            self.from_user.is_active is False
            or self.from_user.profile.deactivated is True
        ):
            logger.info("Already transferred successfully")
            return

        if not self.success and self.retry:
            self.attempted += 1
            self.datetime_last_attempted = timezone.now()
            # cleanup private key placeholders
            data = self.data.copy()
            user_wallet = self.from_user.wallet
            self.from_hedera_account_id = user_wallet.hedera_account_id
            for transfer in data:
                # On the first attempt we always need to set private key, on subsequent attempts, it should already be available if it was unsuccessful
                if (
                    self.attempted == 1
                    or transfer["fromAccount"]["privateKey"]
                    == settings.PRIVATE_KEY_PLACEHOLDER
                    or transfer["fromAccount"]["privateKey"] is None
                ) and user_private_key is not None:
                    transfer["fromAccount"]["privateKey"] = user_private_key

                # Also we can't make the transfer if the private is missing
                if (
                    transfer["fromAccount"]["privateKey"] is not None
                    and transfer["fromAccount"]["privateKey"]
                    != settings.PRIVATE_KEY_PLACEHOLDER
                ):
                    res = requests.post(
                        "{}/token/transfer".format(settings.H_HTS_API_URL),
                        json=transfer,
                    )
                    if res.ok:
                        self.success = True
                        self.datetime_success = timezone.now()
                    else:
                        self.error = res.text
                        self.save()
                        return

            if self.success:
                # If transfer is successful we can remove the private keys
                self.data = hedera_utils.remove_private_keys_from_transaction(self)

                # Here we pick up the info from the hedera network
                # if that fails we just update the balance
                try:
                    user_balance = hedera_utils.check_token_balance_on_hedera_network(
                        user_wallet.user
                    )
                except hedera_utils.CheckTokenBalanceError:
                    user_balance = user_wallet.token_balance - self.value
                user_wallet.token_balance = user_balance
                user_wallet.token_balance_last_update = timezone.now()
                user_wallet.save()

                # We need to update the balance for other accounts in our system
                # if the transfer was successful
                for transfer in self.data:
                    for to_account in transfer["toAccounts"]:
                        try:
                            transfer_wallet = Wallet.objects.get(
                                hedera_account_id=to_account["accountId"]
                            )
                        except Wallet.DoesNotExist:
                            logger.info(
                                "Wallet transferred to does not exist on platform"
                            )
                        else:
                            try:
                                transfer_wallet.token_balance = hedera_utils.check_token_balance_on_hedera_network(
                                    transfer_wallet.user
                                )
                            except hedera_utils.CheckTokenBalanceError:
                                transfer_wallet.token_balance = (
                                    transfer_wallet.token_balance - to_account["amount"]
                                )
                            transfer_wallet.save()

            self.save()
        else:
            logger.info("Already transferred successfully")


class Settings(models.Model):
    receive_weekly_digest = models.BooleanField(default=True)
    receive_monthly_digest = models.BooleanField(default=True)

    notify_fan_mail = models.BooleanField(default=True)
    notify_review = models.BooleanField(default=True)
    notify_tip = models.BooleanField(default=True)
    notify_downloads = models.BooleanField(default=True)
    notify_fan = models.BooleanField(default=True)
    notify_play = models.BooleanField(default=True)
    notify_events = models.BooleanField(default=True)

    notify_fan_threshold = models.IntegerField(default=5)
    notify_play_threshold = models.IntegerField(default=10)

    def get_total_stripe_fee(self):
        total = 0
        for download in self.profile.get_downloads_unpaid():  # type: ignore
            total += download.stripe_fee()
        return utils.pretty_money(total)


class Person(CachingMixin, models.Model):
    objects = CachingManager()

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile = models.OneToOneField(
        Profile, related_name="_person", on_delete=models.CASCADE
    )
    organizations = models.ManyToManyField("Organization", blank=True)

    ipaddr = models.GenericIPAddressField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)

    # if they got a temporary pass from an email this'll be true till
    # they change it
    should_change_pass = models.BooleanField(default=False)

    # if their account has been verified via email
    verified = models.BooleanField(default=False)
    verification_key = models.CharField(max_length=32, null=True)

    # if user has not passed the social join_social page redirect there
    passed_join_social = models.BooleanField(default=False)

    # profile account that user is currently using
    # TODO: ensure db structure reflects changes on 2.2 upgrade
    view = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL)

    jam_now = models.BooleanField(default=False)

    is_musician = models.BooleanField(default=False)
    musician = models.OneToOneField("Musician", null=True, on_delete=models.SET_NULL)
    producer = models.BooleanField(default=False)
    engineer = models.BooleanField(default=False)

    def __str__(self):
        return self.profile.name

    def get_bands(self):
        return [
            m.group for m in Membership.objects.filter(person=self, group__is_band=True)
        ]

    def get_groups(self):
        return [m.group for m in Membership.objects.filter(person=self)]

    def view_is_person(self):
        return self.view.is_person()

    def view_is_band(self):
        return self.view.is_band()

    def jsonify(self, request):
        return self.profile.jsonify(request)

    def get_accounts(self):
        accs = [
            mem.group.profile
            for mem in Membership.objects.filter(person=self, admin=True)
        ]
        if self.profile not in accs:
            return [self.profile] + accs
        else:
            return accs

    class Meta:
        verbose_name_plural = "people"
        get_latest_by = "last_login"


class Musician(models.Model):
    teacher = models.BooleanField(default=False)
    write_music = models.BooleanField(default=False)
    join_band = models.BooleanField(default=False)
    dj = models.BooleanField(default=False)
    profileID = models.SlugField(max_length=100)
    instruments = models.ManyToManyField(
        "Instrument", blank=True, related_name="musicians"
    )

    def __str__(self):
        return self.profileID

    def get_instrument(self):
        try:
            return self.instruments.all()[0].name
        except:
            return ""

    def get_profile(self):
        return Profile.objects.get(person__musician=self)


class Organization(models.Model):
    # TODO: this needs to accept artists and fans as well for polymorphous merge
    # this can potentially be done using 'organization' since its already
    # linked to the artist profile and we are now accepting that artists can
    # have many managers (members)
    users = models.ManyToManyField(User, related_name="organization", blank=True)
    profile = models.OneToOneField(
        Profile, related_name="organization", on_delete=models.CASCADE
    )
    members = models.ManyToManyField(Person, through="Membership")
    pending = models.ManyToManyField(Person, related_name="pending_organizations")

    homepage = models.CharField(max_length=200, blank=True)

    # These can all be deleted if we can get the profile type through other means
    is_band = models.BooleanField(default=False)
    band = models.OneToOneField(
        "Band", null=True, related_name="organization", on_delete=models.SET_NULL
    )
    is_venue = models.BooleanField(default=False)
    venue = models.OneToOneField(
        "Venue", null=True, related_name="organization", on_delete=models.SET_NULL
    )
    is_label = models.BooleanField(default=False)
    label = models.OneToOneField(
        "Label", null=True, related_name="organization", on_delete=models.SET_NULL
    )
    is_artist = models.BooleanField(default=False)
    is_fan = models.BooleanField(default=False)

    # Instead of band and venue here, just use profile, since
    # poly branch already supports interchanging types

    def __str__(self):
        return self.profile.name

    def jsonify(self, request):
        return self.profile.jsonify(request)

    def user_is_admin_or_profile_owner(self, view):
        """
        Given a view (Person.view) test if the user can manage the org
        or membership
        """
        return bool(
            self.profile == view
            or Membership.objects.filter(
                admin=True, group=self, person__profile=view
            ).count()
        )

    def add_member(self, person, is_admin=True):
        self.users.add(person.user)
        person.organizations.add(self)
        if person in self.pending.all():
            self.pending.remove(person)
        ml = Membership.objects.create(person=person, group=self)
        ml.admin = is_admin
        ml.save()
        self.save()

    def update_share_split(self, person, share):
        # Remove pending membership or membership
        try:
            mem = Membership.objects.get(person=person, group=self)
        except Membership.DoesNotExist:
            pass
        else:
            total_share = int(
                sum([m.revenue_split for m in Membership.objects.filter(group=self)])
            )
            if total_share <= 100:
                logger.info(
                    "Updated share split %s for person id %s", share, mem.person_id
                )
                mem.revenue_split = share
                mem.save()

    def remove_member(self, person):
        # Remove pending membership or membership
        try:
            mem = Membership.objects.get(person=person, group=self)
        except Membership.DoesNotExist:
            if person in self.pending.all():
                self.pending.remove(person)
        else:
            mem.delete()
        person.organizations.remove(self)
        person.save()

    def make_pending_member(self, person):
        person.organizations.add(self)
        self.pending.add(person)

    def set_type_and_save(self, type):
        """
        http://stackoverflow.com/questions/12754024/onetoonefield-and-deleting
        Due to Organization being dependant on the underlying object
        we need to set the onetoone field to null and save before
        finalizing the action (Otherwise Organization gets deleted
        as well)

        We set type and 'save' because we are creating related objects
        and will always want to save to prevent objects being created without
        reference to a parent.

        """
        if type == "artist":
            self.is_artist = True
            self.is_fan = False
            self.is_venue = False
            self.is_band = False
            self.is_label = False
            if self.label:
                label = self.label
                self.label = None
                self.save()
                label.delete()
            if self.venue:
                venue = self.venue
                self.venue = None
                self.save()
                venue.delete()
            if self.band:
                band = self.band
                self.band = None
                self.save()
                band.delete()
        elif type == "fan":
            self.is_artist = False
            self.is_fan = True
            self.is_venue = False
            self.is_label = False
            self.is_band = False
            if self.venue:
                venue = self.venue
                self.venue = None
                self.save()
                venue.delete()
            if self.label:
                label = self.label
                self.label = None
                self.save()
                label.delete()
            if self.band:
                band = self.band
                self.band = None
                self.save()
                band.delete()
        elif type == "venue":
            self.is_artist = False
            self.is_fan = False
            self.is_venue = True
            self.is_label = False
            self.is_band = False
            if not self.venue:
                self.venue = Venue.objects.create()
            if self.band:
                band = self.band
                self.band = None
                self.save()
                band.delete()
            if self.label:
                label = self.label
                self.label = None
                self.save()
                label.delete()
        elif type == "band":
            self.is_artist = False
            self.is_fan = False
            self.is_venue = False
            self.is_band = True
            if not self.band:
                self.band = Band.objects.create()
            if self.venue:
                venue = self.venue
                self.venue = None
                self.save()
                venue.delete()
            if self.label:
                label = self.label
                self.label = None
                self.save()
                label.delete()
        elif type == "label":
            self.is_artist = False
            self.is_fan = False
            self.is_venue = False
            self.is_band = False
            self.is_label = True
            if not self.label:
                self.label = Label.objects.create()
            if self.venue:
                venue = self.venue
                self.venue = None
                self.save()
                venue.delete()
            if self.band:
                band = self.band
                self.band = None
                self.save()
                band.delete()
        self.save()

    def get_type(self):
        assert any(
            [self.is_artist, self.is_fan, self.is_venue, self.is_band, self.is_label]
        )
        if self.is_artist:
            return "artist"
        elif self.is_fan:
            return "fan"
        elif self.is_venue:
            return "venue"
        elif self.is_band:
            return "band"
        elif self.is_label:
            return "label"

    def get_membership(self):
        "Returns members as a tuple of regular members and admins."
        admins = Membership.objects.filter(group=self, admin=True)
        regulars = Membership.objects.filter(group=self, admin=False)
        admins = [mem.person for mem in admins]
        members = [mem.person for mem in regulars]
        return (members, admins)

    def save(self, *args, **kwargs):
        assert any(
            [self.is_artist, self.is_fan, self.is_venue, self.is_band, self.is_label]
        )
        super().save(*args, **kwargs)


class AbstractOrganization(models.Model):
    def __str__(self):
        try:
            return self.organization.profile.name  # type: ignore
        except Organization.DoesNotExist:
            pass
        return "Organization could not be found"

    def getProfile(self):
        return self.organization.profile  # type: ignore

    class Meta:
        abstract = True


class Band(AbstractOrganization):
    formed_date = models.DateField(auto_now_add=True, null=True)

    class Meta:
        get_latest_by = "formed_date"


class Venue(AbstractOrganization):
    pass


class Label(AbstractOrganization):
    pass


class Fan(models.Model):
    fanee = models.ForeignKey(
        Profile, related_name="from_fan", on_delete=models.CASCADE
    )
    faner = models.ForeignKey(Profile, related_name="to_fan", on_delete=models.CASCADE)
    faned_date = models.DateTimeField(auto_now_add=True, null=True)


def create_feed_for_fan(sender, **kwargs):
    if kwargs["raw"]:
        # This means request is coming in from loaddata
        return
    if kwargs["created"]:
        fan = kwargs["instance"]
        Feed.notify_fan_user(from_profile=fan.faner, to_profile=fan.fanee, item=fan)  # type: ignore


post_save.connect(create_feed_for_fan, Fan)


class DupSlugError(Exception):
    "Raise this if the slug is a dup"
    pass


class Membership(models.Model):
    admin = models.BooleanField(default=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    group = models.ForeignKey(Organization, on_delete=models.CASCADE)
    date_joined = models.DateField(auto_now_add=True, blank=True, null=True)
    revenue_split = models.FloatField(default=0.0)

    def __str__(self):
        return "{} - {}{}".format(
            self.person, self.group, self.admin and " (Admin)" or ""
        )

    class Meta:
        get_latest_by = "date_joined"


class Instrument(models.Model):
    name = models.CharField(max_length=60, null=False, blank=False)
    slug = models.SlugField(max_length=60, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        # Slug field wont allow a migration setting it as unique=True,
        # blank=True
        # so we raise an exception if another object is found with the same
        # slug
        if Instrument.objects.filter(slug=self.slug).count() > 1:
            raise DupSlugError(self.slug)
        super().save(*args, **kwargs)


class Genre(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        # Slug field wont allow a migration setting it as unique=True,
        # blank=True
        # so we raise an exception if another object is found with the same
        # slug
        if Genre.objects.filter(slug=self.slug).count() > 1:
            raise DupSlugError(self.slug)
        super().save(*args, **kwargs)


class CommenterEqualsProfileOwnerError(Exception):
    "Raise this if profile_commenter equals profile owner"
    pass


# TODO: test this
def get_status_update_limit():
    return models.Q(app_label="media", model="song") | models.Q(
        app_label="media", model="album"
    )


class StatusUpdate(models.Model):
    status = models.CharField(max_length=255)
    profile = models.ForeignKey(
        Profile, related_name="updates", on_delete=models.CASCADE
    )
    update_date = models.DateTimeField(auto_now_add=True, null=True)

    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content page",
        limit_choices_to=get_status_update_limit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    object_id = models.PositiveIntegerField(verbose_name="related object", null=True,)
    profile_commenter = models.ForeignKey(
        Profile,
        related_name="comments",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    content_object = fields.GenericForeignKey("content_type", "object_id")

    class Meta:
        get_latest_by = "update_date"

    def __str__(self):
        return self.status[:20]

    def save(self, *args, **kwargs):
        """
        Raise an exception if profile_commenter == profile owner
        Some pseudo test code, haven't got around to adding tests for this
        module yet

        >> from accounts.models import *
        >> andrew=Profile.objects.get(keyword='AndrewAntar')
        >> status_update = StatusUpdate(profile_commenter=andrew,
        >>                              profile=andrew,
        >>                              status='Test')
        >>
        >> # Raises error
        >> with self.assertRaises(CommenterEqualsProfileOwnerError).save():
        >>      status_update.save()
        """
        if self.profile_commenter == self.profile:
            raise CommenterEqualsProfileOwnerError()

        super().save(*args, **kwargs)


def create_feed_for_status_update(sender, **kwargs):
    if kwargs["raw"]:
        # This means request is coming in from loaddata
        return
    if kwargs["created"]:
        update = kwargs["instance"]
        if update.profile_commenter:
            # Send the profile owner a status update
            Feed.notify_status_update(  # type: ignore
                from_profile=update.profile, to_profile=update.profile, item=update
            )
        else:
            # Send fans the update
            for fan in Fan.objects.filter(fanee=update.profile):
                fan_profile = fan.faner
                Feed.notify_status_update(  # type: ignore
                    from_profile=update.profile, to_profile=fan_profile, item=update
                )


post_save.connect(create_feed_for_status_update, StatusUpdate)


class ReviewObjectNotSetError(Exception):
    "Raise this if the review object was not set"
    pass


class ReviewAlreadyExistsError(Exception):
    "Raise this if the user already submitted a review"
    pass


class SingleReviewObjectAllowedError(Exception):
    "Raise this if more than one object is attached to a review"
    pass


class Review(models.Model):
    review = models.TextField()
    profile = models.ForeignKey(
        Profile,
        related_name="reviews",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    song = models.ForeignKey(
        "media.Song",
        related_name="reviews",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    album = models.ForeignKey(
        "media.Album",
        related_name="reviews",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    reviewer = models.ForeignKey(
        Profile, blank=True, null=True, on_delete=models.SET_NULL
    )
    review_date = models.DateTimeField(auto_now_add=True)
    useful = models.IntegerField(default=0)
    stars = models.IntegerField(default=0)

    class Meta:
        get_latest_by = "review_date"

    def owner(self):
        return [x for x in [self.profile, self.album, self.song] if x is not None][0]

    def save(self, *args, **kwargs):
        """
        Some pseudo test code, haven't got around to adding tests for this
        module yet

        TODO: danielnordberg: Add test code Mon Mar  2 16:20:43 EAT 2015

        >> from media.models import *
        >> from accounts.models import *
        >> brian=Profile.objects.filter(name='Brian Antar')[0]
        >> p=Profile.objects.get(pk=21)
        >> newreview=Review.objects.filter(profile=p, reviewer=brian)[0]
        >> # Note: fix this, creating an object like this is not correct
        >> newreview.id = None
        >>
        >> # Raises error
        >> with self.assertRaises(ReviewAlreadyExistsError).save():
        >>   newreview.save()
        >>
        >> # Works
        >> newreview.profile = Profile.objects.all()[0]
        >> newreview.save()
        >>
        >> # Raises error
        >> newreview=Review.objects.filter(profile=p, reviewer=brian)[0]
        >> newreview.song = Song.objects.all()[0]
        >> with self.assertRaises(SingleReviewObjectAllowedError).save():
        >>   newreview.save()
        """
        if len([_f for _f in [self.song, self.album, self.profile] if _f]) != 1:
            raise SingleReviewObjectAllowedError()

        if not self.pk:
            if self.song:
                if Review.objects.filter(
                    reviewer=self.reviewer, song=self.song
                ).count():
                    raise ReviewAlreadyExistsError("Song already reviewed")
            elif self.profile:
                if Review.objects.filter(
                    reviewer=self.reviewer, profile=self.profile
                ).count():
                    raise ReviewAlreadyExistsError("Profile already reviewed")
            elif self.album:
                if Review.objects.filter(
                    reviewer=self.reviewer, album=self.album
                ).count():
                    raise ReviewAlreadyExistsError("Album already reviewed")

        super().save(*args, **kwargs)


def create_feed_for_review(sender, **kwargs):
    if kwargs["raw"]:
        # This means request is coming in from loaddata
        return
    if kwargs["created"]:
        review = kwargs["instance"]

        profile = review.profile

        if review.song:
            profile = review.song.profile

        elif review.album:
            profile = review.album.profile

        Feed.notify_review(  # type: ignore
            from_profile=review.reviewer, to_profile=profile, item=review
        )


post_save.connect(create_feed_for_review, Review)


class Location(models.Model):
    zip_code = models.CharField(max_length=5, blank=True, null=True)
    short_state = models.CharField(max_length=2, blank=True, null=True)
    # latitude, longitude are the only required fields
    lat = models.FloatField()
    lng = models.FloatField()
    city = models.CharField(max_length=20, blank=True, null=True)
    # Short name for country, like "US" or "MX"
    country = models.CharField(max_length=3, blank=True, null=True)
    secondary = models.CharField(max_length=60, blank=True, null=True)
    long_state = models.CharField(max_length=20, blank=True, null=True)
    most_exact = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        if self.secondary:
            return self.secondary
        elif self.most_exact:
            return self.most_exact

    def country_name(self):
        if self.country:
            return COUNTRIES[self.country]
        else:
            return None

    def jsonify(self):
        return {"name": self.secondary, "lat": self.lat, "lng": self.lng}


class SongFanEvent(models.Model):
    faner = models.ForeignKey(
        Profile, related_name="song_fan_events", on_delete=models.CASCADE
    )
    faned_date = models.DateTimeField(auto_now_add=True, null=True)
    # TODO: ensure db struct is the same after 2.2 change
    faned_song = models.ForeignKey(
        "media.Song", related_name="fan_events", on_delete=models.CASCADE
    )


def create_feed_for_song_fan_event(sender, **kwargs):
    if kwargs["raw"]:
        # This means request is coming in from loaddata
        return
    if kwargs["created"]:
        song_fan_event = kwargs["instance"]
        Feed.notify_fan_song(  # type: ignore
            from_profile=song_fan_event.faner,
            to_profile=song_fan_event.faned_song.profile,
            item=song_fan_event,
        )


post_save.connect(create_feed_for_song_fan_event, SongFanEvent)


class AlbumFanEvent(models.Model):
    faner = models.ForeignKey(
        Profile, related_name="album_fan_events", on_delete=models.CASCADE
    )
    faned_date = models.DateTimeField(auto_now_add=True, null=True)
    faned_album = models.ForeignKey(
        "media.Album", related_name="fan_events", null=False, on_delete=models.CASCADE
    )


def create_feed_for_album_fan_event(sender, **kwargs):
    if kwargs["raw"]:
        # This means request is coming in from loaddata
        return
    if kwargs["created"]:
        album_fan_event = kwargs["instance"]
        Feed.notify_fan_album(  # type: ignore
            from_profile=album_fan_event.faner,
            to_profile=album_fan_event.faned_album.profile,
            item=album_fan_event,
        )


post_save.connect(create_feed_for_album_fan_event, AlbumFanEvent)


class DownloadCharge(models.Model):
    # TODO: ensure db struct is the same after 2.2 change
    profile = models.ForeignKey(
        Profile, related_name="downloads", on_delete=models.CASCADE
    )
    date = models.DateTimeField(auto_now_add=True)
    charge_id = models.CharField(max_length=20, null=True)
    card_used = models.ForeignKey(
        "payment_processing.CreditCard",
        related_name="download_charges",
        null=True,
        on_delete=models.SET_NULL,
    )

    # last4 and cardType are necessary for records, because card_used might be
    # deleted
    last4 = models.CharField(max_length=4, null=True)
    # American Express, Visa, etc.
    cardType = models.CharField(max_length=20, null=True)

    total_price = models.DecimalField(max_digits=6, decimal_places=2)
    # the package id from the download manager
    packageid = models.CharField(max_length=100, null=True)
    # if price is too high, song is marked as suspicious
    suspicious = models.BooleanField(default=False)
    # IMPORTANT: SONG'S TOTAL STRIPE FEE = STRIPE_FEE_PER_SONG + 2.9% OF PRICE
    stripe_fee_per_song = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    def pretty_date(self):
        return utils.ago(self.date)

    def pretty_price(self):
        return "$%.2f" % round(float(self.total_price), 2)

    def songs(self):
        return self.downloads.all()  # type: ignore

    def media_download(self):
        return MediaDownload.objects.get(charge=self)


class MediaDownload(models.Model):
    charge = models.ForeignKey(
        DownloadCharge, related_name="downloads", null=True, on_delete=models.SET_NULL
    )

    price = models.DecimalField(max_digits=5, decimal_places=2)
    # if price is too high, song is marked as suspicious
    suspicious = models.BooleanField(default=False)
    media = models.ForeignKey(
        "media.MusicUpload",
        related_name="download_objects",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    receipt = models.ForeignKey(
        "payment_processing.Receipt",
        related_name="downloads",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def stripe_fee(self):
        if self.price > 0:
            return Decimal(
                (Decimal(settings.STRIPE_FEE_PERCENTAGE) / 100 * self.price)
                + (self.charge.stripe_fee_per_song or 0)
            ).quantize(Decimal("0.01"), rounding=ROUND_UP)

        else:
            return Decimal("0")

    def hearo_fee(self):
        if self.price > 0:
            return (
                (self.price - self.stripe_fee())
                * Decimal(settings.HEARO_FEE_PERCENTAGE)
                / 100
            ).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        else:
            return Decimal(0)

    def commission_total(self):
        if self.price > 0:
            return self.stripe_fee() + self.hearo_fee()
        else:
            return Decimal(0)

    def profit(self):
        return Decimal(self.price - self.commission_total()).quantize(
            Decimal("0.01"), rounding=ROUND_UP
        )

    def pretty_price(self):
        return utils.pretty_money(self.price)

    def pretty_stripe_fee(self):
        return utils.pretty_money(self.stripe_fee())

    def pretty_hearo_fee(self):
        return utils.pretty_money(self.hearo_fee())

    def pretty_commission_total(self):
        return utils.pretty_money(self.commission_total())

    def pretty_profit(self):
        return utils.pretty_money(self.profit())


def create_feed_for_download_link(sender, **kwargs):
    if kwargs["raw"]:
        # This means request is coming in from loaddata
        return
    if kwargs["created"]:
        mediadl = kwargs["instance"]
        try:
            Feed.notify_download_link(  # type: ignore
                from_profile=mediadl.media.profile,
                to_profile=mediadl.charge.profile,
                item=mediadl,
            )
        except Exception as e:
            logger.exception(e, extra={"dl_id": mediadl.id})


post_save.connect(create_feed_for_download_link, MediaDownload)
