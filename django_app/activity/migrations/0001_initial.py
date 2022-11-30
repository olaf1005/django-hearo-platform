# Generated by Django 2.2.9 on 2020-03-02 17:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0002_auto_20200302_1229"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Feed",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "feed_type",
                    models.CharField(
                        choices=[
                            ("fan_mail", "Fan Mail"),
                            ("review", "Review"),
                            ("tip", "Tip"),
                            ("fan_user", "Fan User"),
                            ("fan_song", "Fan Song"),
                            ("fan_album", "Fan Album"),
                            ("played_song", "Played Song"),
                            ("played_album", "Played Album"),
                            ("played_radio", "Played Radio"),
                            ("new_event", "New Event"),
                            ("status_update", "Status Update"),
                            ("download_link", "Download Link"),
                            ("weekly_digest", "Weekly digest"),
                            ("monthly_digest", "Monthly digest"),
                            ("yearly_digest", "Yearly digest"),
                        ],
                        max_length=25,
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                ("delivered_at", models.DateTimeField(null=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.ContentType",
                    ),
                ),
                (
                    "from_profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="accounts.Profile",
                    ),
                ),
                (
                    "to_profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="accounts.Profile",
                    ),
                ),
            ],
        ),
    ]
