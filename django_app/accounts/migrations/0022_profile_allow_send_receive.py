# Generated by Django 2.2.9 on 2021-09-20 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0021_auto_20210831_1328"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="allow_send_receive",
            field=models.BooleanField(default=False),
        ),
    ]
