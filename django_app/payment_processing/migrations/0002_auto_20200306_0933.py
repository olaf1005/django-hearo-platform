# Generated by Django 2.2.9 on 2020-03-06 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payment_processing", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bankinfo",
            name="verified",
            field=models.BooleanField(default=False),
        ),
    ]
