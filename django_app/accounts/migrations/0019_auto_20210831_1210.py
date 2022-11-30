# Generated by Django 2.2.9 on 2021-08-31 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0018_auto_20210831_1112"),
    ]

    operations = [
        migrations.AddField(
            model_name="htstokentransfer",
            name="from_hedera_account_id",
            field=models.CharField(
                max_length=20, null=True, verbose_name="From Hedera Account ID"
            ),
        ),
        migrations.AddField(
            model_name="htstokentransfer",
            name="memo",
            field=models.TextField(null=True, verbose_name="Memo"),
        ),
        migrations.AddField(
            model_name="htstokentransfer",
            name="retry",
            field=models.BooleanField(default=True),
        ),
    ]