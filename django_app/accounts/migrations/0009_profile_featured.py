# Generated by Django 2.2.9 on 2020-05-24 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_auto_20200415_1109"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="featured",
            field=models.BooleanField(default=False),
        ),
    ]
