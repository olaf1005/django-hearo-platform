# Generated by Django 2.2.9 on 2020-04-15 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("media", "0002_auto_20200306_0933"),
    ]

    operations = [
        migrations.RemoveField(model_name="listen", name="payment_date",),
        migrations.AddField(
            model_name="listen",
            name="datetime_processed",
            field=models.DateTimeField(null=True),
        ),
    ]
