# Generated by Django 3.2.7 on 2021-10-24 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0004_userwinpoolteam"),
    ]

    operations = [
        migrations.AddField(
            model_name="userwinpoolteam",
            name="auction_price",
            field=models.IntegerField(default=0),
        ),
    ]
