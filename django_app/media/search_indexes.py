from django.db.models import Q

from haystack import indexes

from .models import Album, Song


class SongIndex(indexes.ModelSearchIndex, indexes.Indexable):
    rank_all = indexes.IntegerField(model_attr="rank_all", default=0)
    rank_today = indexes.IntegerField(model_attr="rank_today", default=0)
    rank_week = indexes.IntegerField(model_attr="rank_week", default=0)
    rank_month = indexes.IntegerField(model_attr="rank_month", default=0)
    rank_year = indexes.IntegerField(model_attr="rank_year", default=0)

    class Meta:
        model = Song

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            Q(deleted=False),
            Q(online=True),
            Q(profile__profile_private=False),
            Q(profile__deactivated=False),
            (Q(profile__user__is_active=True) | Q(profile__user=None)),
        )

    location_country = indexes.CharField(null=True)

    def prepare_location_country(self, obj):
        if obj.profile and obj.profile.location:
            return obj.profile.location.country_name()
        return None

    location = indexes.CharField(null=True)

    def prepare_location(self, obj):
        if obj.profile and obj.profile.location:
            return obj.profile.location.most_exact
        return None

    secondary_location = indexes.CharField(null=True)

    def prepare_secondary_location(self, obj):
        if obj.profile and obj.profile.location:
            return obj.profile.location.secondary
        return None

    created = indexes.DateField()

    def prepare_created(self, obj):
        return obj.upload_date

    genres = indexes.MultiValueField(null=True)

    def prepare_genres(self, obj):
        if obj.profile and obj.profile.genres.count():
            return [str(genre) for genre in obj.profile.genres.all()]
        return None


class AlbumIndex(indexes.ModelSearchIndex, indexes.Indexable):
    title = indexes.CharField()

    rank_all = indexes.IntegerField(model_attr="rank_all")
    rank_today = indexes.IntegerField(model_attr="rank_today")
    rank_week = indexes.IntegerField(model_attr="rank_week")
    rank_month = indexes.IntegerField(model_attr="rank_month")
    rank_year = indexes.IntegerField(model_attr="rank_year")

    location = indexes.CharField(null=True)

    def prepare_location(self, obj):
        if obj.profile and obj.profile.location:
            return obj.profile.location.most_exact
        return None

    location_country = indexes.CharField(null=True)

    def prepare_location_country(self, obj):
        if obj.profile and obj.profile.location:
            return obj.profile.location.country_name()
        return None

    secondary_location = indexes.CharField(null=True)

    def prepare_secondary_location(self, obj):
        if obj.profile and obj.profile.location:
            return obj.profile.location.secondary
        return None

    created = indexes.DateField()

    def prepare_created(self, obj):
        return obj.upload_date

    genres = indexes.MultiValueField()

    def prepare_genres(self, obj):
        if obj.profile and obj.profile.genres.count():
            return [str(genre) for genre in obj.profile.genres.all()]
        return None

    class Meta:
        model = Album

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            Q(deleted=False),
            Q(profile__profile_private=False),
            Q(profile__deactivated=False),
            (Q(profile__user__is_active=True) | Q(profile__user=None)),
        )
