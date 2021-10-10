import logging
from datetime import datetime
from functools import cached_property

import attr
from fitbit import Fitbit

from db.models import ThirdPartyAuth
from lib.fitbot.config import FitbotConfig


class FitbotService:

    config = FitbotConfig()
    unauth_fitbit = Fitbit(
        config.client_id,
        config.client_secret,
        timeout=10,
    )

    @classmethod
    def auth_url(cls):
        url, _ = cls.unauth_fitbit.client.authorize_token_url(
            scope=cls.config.scope,
            redirect_uri="http://localhost/callback"
        )
        return url

    @classmethod
    def is_user_registered(cls, user_id, guild_id):
        return ThirdPartyAuth.objects.filter(
            user_id=user_id, provider=FitbotConfig.provider, guild_id=guild_id
        ).exists()

    @classmethod
    def store_auth_token(cls, user_id, guild_id, code):
        token = cls.unauth_fitbit.client.fetch_access_token(code)
        logging.info(f"TOKEN: {token}")
        third_party_auth = ThirdPartyAuth.objects.create(
            user_id=user_id,
            provider=cls.provider,
            guild_id=guild_id,
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            scope=','.join(token['scope']),
            expires_at=datetime.fromtimestamp(token['expires_at'])
        )
        logging.info(f"AUTH RECORD: {third_party_auth}")

    @classmethod
    def disconnect_user(cls, user_id, guild_id):
        auth = cls.get_user_auth(user_id, guild_id)
        auth.delete()

    @staticmethod
    def get_user_auth(user_id, guild_id):
        auth = ThirdPartyAuth.objects.filter(
            user_id=user_id,
            provider=FitbotConfig.provider,
            guild_id=guild_id,
        ).first()
        if not auth:
            raise LookupError("User fitbit credentials not found")
        return auth

    @staticmethod
    def get_authed_client(user_id=None, guild_id=None, auth=None):
        auth = auth or FitbotService.get_user_auth(user_id, guild_id)
        return Fitbit(
            FitbotConfig.client_id,
            FitbotConfig.client_secret,
            access_token=auth.access_token,
            refresh_token=auth.refresh_token,
            refresh_cb=FitbitTokenRefresher(auth)
        )

    @classmethod
    def get_guild_weekly_stats(cls, guild_id):
        user_auths = ThirdPartyAuth.objects.filter(
            provider=FitbotConfig.provider,
            guild_id=guild_id
        )
        user_stats = [cls.get_user_weekly_stats(auth) for auth in user_auths]
        return GuildWeeklyStats(user_stats)

    @classmethod
    def get_user_weekly_stats(cls, auth):
        client = cls.get_authed_client(auth=auth)
        period = '7d'
        fairly_active = client.time_series("activities/minutesFairlyActive", period=period)
        very_active = client.time_series("activities/minutesVeryActive", period=period)
        steps = client.time_series("activities/steps", period=period)
        distance = client.time_series("activities/distance", period=period)

        logging.info(f"Fairly Active: {fairly_active}")
        logging.info(f"Very Active: {very_active}")
        logging.info(f"Steps: {steps}")
        logging.info(f"Distance: {distance}")

        return UserWeeklyStats(
            user_id=auth.user_id,
            fairly_active=fairly_active,
            very_active=very_active,
            steps=steps,
            distance=distance
        )


@attr.s
class LeaderboardEntry:
    user_id = attr.ib()
    score = attr.ib()


class GuildWeeklyStats:

    def __init__(self, user_stats):
        self.user_stats = user_stats

    @cached_property
    def leaderboard(self):
        return sorted(
            [
                LeaderboardEntry(
                    user_id=user_stat.user_id,
                    score=user_stat.total_active_minutes
                ) for user_stat in self.user_stats
            ],
            key=lambda lb_entry: lb_entry.score,
            reverse=True
        )


class UserWeeklyStats:
    def __init__(self, user_id, fairly_active, very_active, steps, distance):
        self.user_id = user_id
        self.fairly_active_min_data = fairly_active
        self.very_active_min_data = very_active
        self.steps_data = steps
        self.distance_data = distance

    @property
    def total_steps(self):
        return sum(self.steps_data)

    @property
    def total_distance(self):
        return sum(self.distance_data)

    @property
    def total_active_minutes(self):
        # per fitbit docs, active minutes = sum of fairly & very active min
        return sum(self.fairly_active_min_data) + sum(self.very_active_min_data)


class FitbitTokenRefresher:

    def __init__(self, auth):
        self.auth = auth

    def __call__(self, new_token):
        self.auth.refresh_token = new_token['refresh_token']
        self.auth.access_token = new_token['access_token']
        self.auth.expires_at = datetime.fromtimestamp(new_token['expires_at'])
        self.auth.save()
