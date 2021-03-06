# Generated by Django 3.2.7 on 2021-10-23 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0003_thirdpartyauth"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserWinPoolTeam",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("user_id", models.TextField()),
                ("guild_id", models.TextField()),
                ("bdl_team_id", models.TextField()),
                ("team_name", models.TextField()),
            ],
            options={
                "unique_together": {("guild_id", "team_name")},
            },
        ),
    ]
