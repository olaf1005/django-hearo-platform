# Generated by Django 2.2.9 on 2020-08-14 13:45

from django.db import migrations

from utils import normalize_email


def normalize_emails(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    User = apps.get_model("auth", "User")
    for user in User.objects.all():
        try:
            profile = user.person.profile
        except:
            pass
        else:
            normalized_email = normalize_email(user.email)
            profile.email_normalized = normalized_email
            profile.save()


def reverse_normalize_emails(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_auto_20200814_0943"),
    ]

    operations = [
        migrations.RunPython(normalize_emails, reverse_normalize_emails),
    ]
