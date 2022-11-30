# Generated by Django 2.2.9 on 2020-03-02 17:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MusicUpload",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("upload_date", models.DateField(auto_now_add=True, null=True)),
                ("fans", models.PositiveIntegerField(default=0)),
                ("downloads", models.PositiveIntegerField(default=0)),
                ("splash_featured", models.BooleanField()),
                (
                    "download_type",
                    models.CharField(
                        choices=[
                            ("none", "Stream Only"),
                            ("album", "Album Only"),
                            ("free", "Free Download"),
                            ("normal", "Fixed Price"),
                            ("name_price", "Name Your Price"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                (
                    "portion_donated",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=3, null=True
                    ),
                ),
                ("keyword", models.SlugField(max_length=255)),
                ("deleted", models.BooleanField(default=False)),
                ("rank_all", models.IntegerField(default=0)),
                ("rank_today", models.IntegerField(default=0)),
                ("rank_week", models.IntegerField(default=0)),
                ("rank_month", models.IntegerField(default=0)),
                ("rank_year", models.IntegerField(default=0)),
                ("suspicious", models.BooleanField()),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="music",
                        to="accounts.Profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Album",
            fields=[
                ("title", models.CharField(max_length=100)),
                (
                    "full_cover",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/full_album"
                    ),
                ),
                (
                    "medium_cover",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/medium_album"
                    ),
                ),
                (
                    "small_cover",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/small_album"
                    ),
                ),
                ("year_released", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "musicupload_ptr",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name="media_album",
                        serialize=False,
                        to="media.MusicUpload",
                    ),
                ),
                ("available", models.BooleanField(default=False)),
                (
                    "album_cover",
                    models.ImageField(blank=True, null=True, upload_to="images/full"),
                ),
            ],
            bases=("media.musicupload",),
        ),
        migrations.CreateModel(
            name="Video",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("embed_id", models.CharField(max_length=200)),
                ("title", models.CharField(max_length=200)),
                ("upload_date", models.DateField(auto_now_add=True, null=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="videos",
                        to="accounts.Profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Radio",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="radio",
                        to="accounts.Profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Photo",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("upload_date", models.DateField(auto_now_add=True, null=True)),
                ("full_file", models.ImageField(upload_to="images/full")),
                (
                    "thumbnail_file",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/thumbnails"
                    ),
                ),
                (
                    "square_file",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/squares"
                    ),
                ),
                (
                    "profile_file",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/profile_file"
                    ),
                ),
                ("crop_top", models.PositiveIntegerField(blank=True, null=True)),
                ("crop_bottom", models.PositiveIntegerField(blank=True, null=True)),
                ("crop_left", models.PositiveIntegerField(blank=True, null=True)),
                ("crop_right", models.PositiveIntegerField(blank=True, null=True)),
                ("caption", models.CharField(blank=True, max_length=200, null=True)),
                ("processing", models.BooleanField(default=False)),
                ("is_banner", models.BooleanField(default=False)),
                ("is_cover", models.BooleanField(default=False)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.Profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Banner",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "texture",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/textures"
                    ),
                ),
                (
                    "texture_resized",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/textures_resized"
                    ),
                ),
                (
                    "texture_cropped",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/textures_cropped"
                    ),
                ),
                (
                    "texture_chosen",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                ("crop_top", models.PositiveIntegerField(blank=True, null=True)),
                ("crop_bottom", models.PositiveIntegerField(blank=True, null=True)),
                ("crop_left", models.PositiveIntegerField(blank=True, null=True)),
                ("crop_right", models.PositiveIntegerField(blank=True, null=True)),
                ("font", models.CharField(blank=True, max_length=100, null=True)),
                ("display_title", models.BooleanField(default=True)),
                ("display_genre", models.BooleanField(default=True)),
                ("display_instrument", models.BooleanField(default=True)),
                ("display_location", models.BooleanField(default=True)),
                ("display_bar", models.BooleanField(default=False)),
                (
                    "texture_temp",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/textures_temp"
                    ),
                ),
                (
                    "texture_temp_resized",
                    models.ImageField(
                        blank=True, null=True, upload_to="images/textures_temp"
                    ),
                ),
                (
                    "photo",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="banner",
                        to="media.Photo",
                    ),
                ),
                (
                    "profile",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="banner",
                        to="accounts.Profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Song",
            fields=[
                ("file", models.FileField(null=True, upload_to="")),
                ("processing", models.BooleanField()),
                ("online", models.BooleanField()),
                ("visible", models.BooleanField()),
                ("title", models.CharField(max_length=100)),
                ("track_num", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("length", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "musicupload_ptr",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name="media_song",
                        serialize=False,
                        to="media.MusicUpload",
                    ),
                ),
                ("state_info", models.CharField(max_length=1000, null=True)),
                ("isrc", models.CharField(blank=True, max_length=12, null=True)),
                ("upc_ean", models.CharField(blank=True, max_length=12, null=True)),
                (
                    "album",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="songs",
                        to="media.Album",
                    ),
                ),
            ],
            options={"ordering": ("album", "track_num"),},
            bases=("media.musicupload",),
        ),
        migrations.CreateModel(
            name="Listen",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("seconds", models.PositiveIntegerField()),
                ("datetime", models.DateTimeField(auto_now_add=True, null=True)),
                ("payment_date", models.DateTimeField(default=None, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="listens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "song",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="listens",
                        to="media.Song",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="album",
            name="cover",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="album",
                to="media.Photo",
            ),
        ),
    ]
