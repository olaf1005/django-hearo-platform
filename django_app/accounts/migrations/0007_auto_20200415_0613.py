# Generated by Django 2.2.9 on 2020-04-15 10:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("media", "0002_auto_20200306_0933"),
        ("accounts", "0006_tokentransfer_wallet_walletrecovery"),
    ]

    operations = [
        migrations.AddField(
            model_name="tokentransfer",
            name="attempted",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="tokentransfer",
            name="datetime_last_attempted",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="tokentransfer",
            name="listen",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="payments_made",
                to="media.Listen",
            ),
        ),
        migrations.AlterField(
            model_name="tokentransfer",
            name="from_user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="user_payments_made",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="tokentransfer",
            name="to_user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="user_payments_received",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
