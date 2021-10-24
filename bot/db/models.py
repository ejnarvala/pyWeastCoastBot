from django.db import models


class Reminder(models.Model):
    user_id = models.TextField()
    channel_id = models.TextField()
    message_id = models.TextField()
    message = models.TextField(default=None, blank=True, null=True)
    remind_time = models.DateTimeField()

    def __str__(self) -> str:
        return f"Reminder({self.remind_time})"


class ThirdPartyAuth(models.Model):
    class Meta:
        unique_together = [["user_id", "provider", "guild_id"]]

    user_id = models.TextField()
    provider = models.TextField()
    guild_id = models.TextField()
    access_token = models.TextField()
    refresh_token = models.TextField()
    scope = models.TextField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserWinPoolTeam(models.Model):
    class Meta:
        unique_together = [["guild_id", "team_name"]]

    user_id = models.TextField()
    guild_id = models.TextField()
    bdl_team_id = models.TextField()
    team_name = models.TextField()
    auction_price = models.IntegerField()
