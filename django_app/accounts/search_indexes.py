from django.db.models import Q

from haystack import indexes

from .models import Profile


class ProfileIndex(indexes.ModelSearchIndex, indexes.Indexable):
    class Meta:
        model = Profile

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            Q(profile_private=False),
            Q(deactivated=False),
            (Q(user__is_active=True) | Q(user=None)),
        )

    rank_all = indexes.IntegerField(model_attr="rank_all", default=0)
    rank_today = indexes.IntegerField(model_attr="rank_today", default=0)
    rank_week = indexes.IntegerField(model_attr="rank_week", default=0)
    rank_month = indexes.IntegerField(model_attr="rank_month", default=0)
    rank_year = indexes.IntegerField(model_attr="rank_year", default=0)

    genres = indexes.MultiValueField()

    def prepare_genres(self, obj):
        return [str(genre) for genre in obj.genres.all()]

    created = indexes.DateField(null=True)

    def prepare_created(self, obj):
        if obj.user:
            return obj.user.date_joined.date()
        else:
            if obj.person_set.count():
                return obj.person_set.all()[0].user.date_joined.date()
            elif obj.is_orgo():
                if obj.organization.person_set.count():
                    return obj.organization.person_set.all()[0].user.date_joined.date()
            # Some older objects aren't associated with a person object (at
            # least on staging)
            return None

    location = indexes.CharField()

    def prepare_location(self, obj):
        # Some profile objects dont have a location, e.g. bands
        if obj.location:
            return obj.location.most_exact

    location_country = indexes.CharField()

    def prepare_location_country(self, obj):
        # Some profile objects dont have a location, e.g. bands
        if obj.location:
            return obj.location.country_name()

    secondary_location = indexes.CharField(null=True)

    def prepare_secondary_location(self, obj):
        if obj.location:
            return obj.location.secondary
        return None

    is_musician = indexes.BooleanField()

    def prepare_is_musician(self, obj):
        if obj.is_artist():
            person = obj.person
            if person:
                return person.is_musician
        return False

    is_producer = indexes.BooleanField()

    def prepare_is_producer(self, obj):
        if obj.is_artist():
            person = obj.person
            if person:
                return person.producer
        return False

    is_engineer = indexes.BooleanField()

    def prepare_is_engineer(self, obj):
        if obj.is_artist():
            person = obj.person
            if person:
                return person.engineer
        return False

    is_band = indexes.BooleanField()

    def prepare_is_band(self, obj):
        if obj.is_orgo():
            return obj.organization.is_band
        return False

    is_venue = indexes.BooleanField()

    def prepare_is_venue(self, obj):
        if obj.is_orgo():
            return obj.organization.is_venue
        return False

    is_label = indexes.BooleanField()

    def prepare_is_label(self, obj):
        if obj.is_orgo():
            return obj.organization.is_label
        return False

    teacher = indexes.BooleanField()

    def prepare_teacher(self, obj):
        person = obj.person
        if person:
            if person.is_musician:
                return person.musician.teacher
        return False

    write_music = indexes.BooleanField()

    def prepare_write_music(self, obj):
        person = obj.person
        if person:
            if person.is_musician:
                return person.musician.write_music
        return False

    join_band = indexes.BooleanField()

    def prepare_join_band(self, obj):
        person = obj.person
        if person:
            if person.is_musician:
                return person.musician.join_band
        return False

    dj = indexes.BooleanField()

    def prepare_dj(self, obj):
        person = obj.person
        if person:
            if person.is_musician:
                return person.musician.dj
        return False

    instruments = indexes.MultiValueField()

    def prepare_instruments(self, obj):
        person = obj.person
        if person:
            if person.is_musician:
                return [str(inst) for inst in person.musician.instruments.all()]
