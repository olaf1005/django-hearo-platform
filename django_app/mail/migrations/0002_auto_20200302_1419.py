# Generated by Django 2.2.9 on 2020-03-02 19:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message", name="read", field=models.BooleanField(default=False),
        ),
    ]
