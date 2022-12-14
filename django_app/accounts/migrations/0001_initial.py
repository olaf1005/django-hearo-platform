# Generated by Django 2.2.9 on 2020-03-02 17:29

import accounts.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AlbumFanEvent",
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
                ("faned_date", models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Band",
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
                ("formed_date", models.DateField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="DownloadCharge",
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
                ("date", models.DateTimeField(auto_now_add=True)),
                ("charge_id", models.CharField(max_length=20, null=True)),
                ("last4", models.CharField(max_length=4, null=True)),
                ("cardType", models.CharField(max_length=20, null=True)),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=6)),
                ("packageid", models.CharField(max_length=100, null=True)),
                ("suspicious", models.BooleanField()),
                (
                    "stripe_fee_per_song",
                    models.DecimalField(decimal_places=2, max_digits=5, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Fan",
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
                ("faned_date", models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Genre",
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
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Instrument",
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
                ("name", models.CharField(max_length=60)),
                ("slug", models.SlugField(max_length=60, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Label",
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
            ],
        ),
        migrations.CreateModel(
            name="Location",
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
                ("zip_code", models.CharField(blank=True, max_length=5, null=True)),
                ("short_state", models.CharField(blank=True, max_length=2, null=True)),
                ("lat", models.FloatField()),
                ("lng", models.FloatField()),
                ("city", models.CharField(blank=True, max_length=20, null=True)),
                ("country", models.CharField(blank=True, max_length=3, null=True)),
                ("secondary", models.CharField(blank=True, max_length=60, null=True)),
                ("long_state", models.CharField(blank=True, max_length=20, null=True)),
                ("most_exact", models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="MediaDownload",
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
                ("price", models.DecimalField(decimal_places=2, max_digits=5)),
                ("suspicious", models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name="Membership",
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
                ("admin", models.BooleanField(default=False)),
                ("date_joined", models.DateField(auto_now_add=True, null=True)),
                ("revenue_split", models.FloatField(default=0.0)),
            ],
        ),
        migrations.CreateModel(
            name="Musician",
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
                ("teacher", models.BooleanField()),
                ("write_music", models.BooleanField()),
                ("join_band", models.BooleanField()),
                ("dj", models.BooleanField()),
                ("profileID", models.SlugField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Organization",
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
                ("homepage", models.CharField(blank=True, max_length=200)),
                ("is_band", models.BooleanField()),
                ("is_venue", models.BooleanField()),
                ("is_label", models.BooleanField()),
                ("is_artist", models.BooleanField()),
                ("is_fan", models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name="Person",
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
                ("ipaddr", models.GenericIPAddressField(blank=True, null=True)),
                ("last_login", models.DateTimeField(blank=True, null=True)),
                ("should_change_pass", models.BooleanField(default=False)),
                ("verified", models.BooleanField(default=False)),
                ("verification_key", models.CharField(max_length=32, null=True)),
                ("jam_now", models.BooleanField(default=False)),
                ("is_musician", models.BooleanField(default=False)),
                ("producer", models.BooleanField(default=False)),
                ("engineer", models.BooleanField(default=False)),
            ],
            options={"verbose_name_plural": "people",},
        ),
        migrations.CreateModel(
            name="Profile",
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
                ("deactivated", models.BooleanField(default=False)),
                ("keyword", models.SlugField(max_length=100, null=True, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("short_name", models.CharField(max_length=50)),
                ("biography", models.TextField(blank=True, null=True)),
                ("profile_layout_settings", models.CharField(max_length=500)),
                ("influences", models.TextField(blank=True, null=True)),
                ("experience", models.TextField(blank=True, null=True)),
                ("goals", models.TextField(blank=True, null=True)),
                ("location_set", models.BooleanField()),
                ("splash_featured", models.BooleanField()),
                ("p_address1", models.CharField(blank=True, max_length=200, null=True)),
                ("p_address2", models.CharField(blank=True, max_length=200, null=True)),
                ("p_state", models.CharField(blank=True, max_length=2, null=True)),
                ("p_zip", models.CharField(blank=True, max_length=10, null=True)),
                ("p_city", models.CharField(blank=True, max_length=200, null=True)),
                (
                    "p_country",
                    models.CharField(blank=True, default="", max_length=60, null=True),
                ),
                ("is_international", models.BooleanField(default=True)),
                ("signed_artist_agreement", models.BooleanField(default=False)),
                ("signed_new_artist_agreement", models.BooleanField(default=False)),
                ("signed_new_tc_aggreement", models.BooleanField(default=False)),
                ("down_to_jam", models.BooleanField()),
                ("on_air", models.BooleanField()),
                (
                    "credit",
                    models.DecimalField(decimal_places=3, default=0, max_digits=15),
                ),
                ("fanmail_private", models.BooleanField(default=False)),
                ("downloads_private", models.BooleanField(default=False)),
                ("profile_private", models.BooleanField(default=False)),
                (
                    "default_download_format",
                    models.CharField(
                        choices=[
                            ("mp3_320", "MP3 320"),
                            ("mp3_v0", "MP3 245"),
                            ("mp3_v2", "MP3 190"),
                            ("flac", "FLAC"),
                        ],
                        max_length=7,
                    ),
                ),
                ("rank_all", models.IntegerField(default=0)),
                ("rank_today", models.IntegerField(default=0)),
                ("rank_week", models.IntegerField(default=0)),
                ("rank_month", models.IntegerField(default=0)),
                ("rank_year", models.IntegerField(default=0)),
                ("rank_dir", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Review",
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
                ("review", models.TextField()),
                ("review_date", models.DateTimeField(auto_now_add=True)),
                ("useful", models.IntegerField(default=0)),
                ("stars", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Settings",
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
                ("receive_weekly_digest", models.BooleanField(default=True)),
                ("receive_monthly_digest", models.BooleanField(default=True)),
                ("notify_fan_mail", models.BooleanField(default=True)),
                ("notify_review", models.BooleanField(default=True)),
                ("notify_tip", models.BooleanField(default=True)),
                ("notify_downloads", models.BooleanField(default=True)),
                ("notify_fan", models.BooleanField(default=True)),
                ("notify_play", models.BooleanField(default=True)),
                ("notify_events", models.BooleanField(default=True)),
                ("notify_fan_threshold", models.IntegerField(default=5)),
                ("notify_play_threshold", models.IntegerField(default=10)),
            ],
        ),
        migrations.CreateModel(
            name="SongFanEvent",
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
                ("faned_date", models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Venue",
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
            ],
        ),
        migrations.CreateModel(
            name="StatusUpdate",
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
                ("status", models.CharField(max_length=255)),
                ("update_date", models.DateTimeField(auto_now_add=True, null=True)),
                (
                    "object_id",
                    models.PositiveIntegerField(
                        null=True, verbose_name="related object"
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to=accounts.models.get_status_update_limit,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contenttypes.ContentType",
                        verbose_name="content page",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="updates",
                        to="accounts.Profile",
                    ),
                ),
                (
                    "profile_commenter",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="comments",
                        to="accounts.Profile",
                    ),
                ),
            ],
        ),
    ]
