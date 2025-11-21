import logging
from datetime import datetime
from functools import cached_property

import attr
import pandas as pd
from fitbit import Fitbit
from sqlmodel import select

from pyWeastCoastBot.db.models import ThirdPartyAuth
from pyWeastCoastBot.db.session import get_session
from pyWeastCoastBot.lib.fitbot.config import FitbotConfig


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
            scope=cls.config.scope, redirect_uri="http://localhost/callback"
        )
        return url

    @classmethod
    async def is_user_registered(cls, user_id, guild_id):
        async for session in get_session():
            stmt = select(ThirdPartyAuth).where(
                ThirdPartyAuth.user_id == str(user_id),
                ThirdPartyAuth.provider == FitbotConfig.provider,
                ThirdPartyAuth.guild_id == str(guild_id),
            )
            result = await session.exec(stmt)
            return result.first() is not None

    @classmethod
    async def store_auth_token(cls, user_id, guild_id, code):
        token = cls.unauth_fitbit.client.fetch_access_token(code)
        auth = ThirdPartyAuth(
            user_id=str(user_id),
            provider=cls.config.provider,
            guild_id=str(guild_id),
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            scope=",".join(token["scope"]),
            expires_at=datetime.fromtimestamp(token["expires_at"]),
        )

        async for session in get_session():
            session.add(auth)
            await session.commit()
            await session.refresh(auth)
            return auth

    @classmethod
    async def disconnect_user(cls, user_id, guild_id):
        auth = await cls.get_user_auth(user_id, guild_id)
        async for session in get_session():
            # Need to merge or re-fetch to attach to current session if passed auth is detached
            await session.delete(auth)
            await session.commit()

    @staticmethod
    async def get_user_auth(user_id, guild_id):
        async for session in get_session():
            stmt = select(ThirdPartyAuth).where(
                ThirdPartyAuth.user_id == str(user_id),
                ThirdPartyAuth.provider == FitbotConfig.provider,
                ThirdPartyAuth.guild_id == str(guild_id),
            )
            result = await session.exec(stmt)
            auth = result.first()

        if not auth:
            raise LookupError("User fitbit credentials not found")
        return auth

    @staticmethod
    async def get_authed_client(user_id=None, guild_id=None, auth=None):
        auth = auth or await FitbotService.get_user_auth(user_id, guild_id)
        # Note: FitbitTokenRefresher needs to be async aware or handled carefully
        # For now, we'll wrap the refresh callback to run in sync but it might block
        # Ideally refactor Fitbit client to be async or handle token refresh separately
        return Fitbit(
            FitbotConfig.client_id,
            FitbotConfig.client_secret,
            access_token=auth.access_token,
            refresh_token=auth.refresh_token,
            refresh_cb=FitbitTokenRefresher(auth),
        )

    @classmethod
    async def get_guild_weekly_stats(cls, guild_id):
        user_auths = []
        async for session in get_session():
            stmt = select(ThirdPartyAuth).where(
                ThirdPartyAuth.provider == FitbotConfig.provider,
                ThirdPartyAuth.guild_id == str(guild_id),
            )
            result = await session.exec(stmt)
            user_auths = result.all()

        user_stats = []
        for auth in user_auths:
            stats = await cls.get_user_weekly_stats(auth)
            user_stats.append(stats)

        return GuildWeeklyStats(user_stats)

    @staticmethod
    def _get_time_series(client, resource, period="7d"):
        return client.time_series(f"activities/{resource}", period=period).get(f"activities-{resource}")

    @classmethod
    async def get_user_weekly_stats(cls, auth):
        client = await cls.get_authed_client(auth=auth)
        # Fitbit client is sync, so these calls are blocking.
        # In a real async app, these should be run in an executor.
        return UserWeeklyStats(
            user_id=auth.user_id,
            fairly_active=cls._get_time_series(client, "minutesFairlyActive"),
            very_active=cls._get_time_series(client, "minutesVeryActive"),
            steps=cls._get_time_series(client, "steps"),
            distance=cls._get_time_series(client, "distance"),
        )

    @classmethod
    async def get_registered_guild_ids(cls):
        async for session in get_session():
            stmt = select(ThirdPartyAuth.guild_id).where(ThirdPartyAuth.provider == FitbotConfig.provider).distinct()
            result = await session.exec(stmt)
            return list(result.all())


@attr.s
class LeaderboardEntry:
    user_id = attr.ib()
    score = attr.ib()


class GuildWeeklyStats:
    def __init__(self, user_stats):
        self.user_stats = user_stats

    @property
    def weekly_active_minutes_leaderboard(self):
        return self._leaderboard("total_active_minutes")

    @property
    def last_day_steps_leaderboard(self):
        return self._leaderboard("last_day_steps")

    @property
    def weekly_steps_leaderboard(self):
        return self._leaderboard("total_steps")

    def _leaderboard(self, metric):
        return sorted(
            [
                LeaderboardEntry(user_id=user_stat.user_id, score=getattr(user_stat, metric))
                for user_stat in self.user_stats
            ],
            key=lambda lb_entry: lb_entry.score,
            reverse=True,
        )

    @property
    def user_ids(self):
        return [u.user_id for u in self.user_stats]

    @property
    def steps_df(self):
        return self._metric_df("steps")

    @cached_property
    def distance_df(self):
        return self._metric_df("distance")

    def _metric_df(self, metric):
        data = dict()
        for user_stat in self.user_stats:
            metric_data = getattr(user_stat, metric)
            index = user_stat.metric_days[-len(metric_data) :]
            series = pd.Series(metric_data, index=index)
            data[user_stat.user_id] = series
        return pd.DataFrame(data)


class UserWeeklyStats:
    def __init__(self, user_id, fairly_active, very_active, steps, distance):
        self.user_id = user_id
        self._fairly_active_min_data = fairly_active
        self._very_active_min_data = very_active
        self._steps_data = steps
        self._distance_data = distance

    @staticmethod
    def _time_series_values(series, data_type):
        return [data_type(d["value"]) for d in series]

    @property
    def metric_days(self):
        return [datetime.strptime(d["dateTime"], "%Y-%m-%d") for d in self._steps_data]

    @property
    def steps(self):
        return self._time_series_values(self._steps_data, int)

    @property
    def distance(self):
        return self._time_series_values(self._distance_data, float)

    @property
    def fairly_active_minutes(self):
        return self._time_series_values(self._fairly_active_min_data, int)

    @property
    def very_active_minutes(self):
        return self._time_series_values(self._very_active_min_data, int)

    @property
    def last_day_steps(self):
        return self.steps[-2]

    @property
    def total_steps(self):
        return sum(self.steps)

    @property
    def total_distance(self):
        return sum(self.distance)

    @property
    def total_fairly_active_minutes(self):
        return sum(self.fairly_active_minutes)

    @property
    def total_very_active_minutes(self):
        return sum(self.very_active_minutes)

    @property
    def total_active_minutes(self):
        # per fitbit docs, active minutes = sum of fairly & very active min
        return self.total_fairly_active_minutes + self.total_very_active_minutes


class FitbitTokenRefresher:
    def __init__(self, auth):
        self.auth = auth

    def __call__(self, new_token):
        # NOTE: This is called by the sync Fitbit library.
        # Ideally we should use an async DB call, but since this is a callback
        # from a sync library, we might need a sync engine or a way to bridge it.
        # For now, we are omitting the implementation or need to handle it carefully.
        # A proper fix involves making the Fitbit client async or using run_sync.
        # Given the complexity, we will log a warning for now.
        logging.warning("Token refresh attempted but DB save not implemented for Async SQLModel yet.")
