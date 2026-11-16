import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from functools import cached_property

import attr
import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlmodel import select

from pyWeastCoastBot.db.models import ThirdPartyAuth
from pyWeastCoastBot.db.session import get_session
from pyWeastCoastBot.lib.fitbot.config import FitbotConfig

logger = logging.getLogger(__name__)


class FitbotService:
    config = FitbotConfig()
    api_endpoint = "https://health.googleapis.com/$discovery/rest?version=v4"
    provider = "google_health"
    pending_flows = {}

    @classmethod
    def _oauth_flow(cls):
        client_config = {
            "web": {
                "client_id": cls.config.client_id,
                "client_secret": cls.config.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [cls.config.redirect_uri],
            }
        }
        return google_auth_oauthlib.flow.Flow.from_client_config(client_config, scopes=cls.config.scope)

    @classmethod
    def auth_url(cls, user_id, guild_id):
        flow = cls._oauth_flow()
        flow.redirect_uri = cls.config.redirect_uri
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )
        cls.pending_flows[(str(user_id), str(guild_id))] = flow
        return authorization_url

    @classmethod
    def _exchange_code(cls, code, flow):
        flow.redirect_uri = cls.config.redirect_uri
        flow.fetch_token(code=code)
        credentials = flow.credentials
        granted_scopes = set(credentials.granted_scopes or [])
        if cls.config.activity_scope not in granted_scopes:
            raise PermissionError("Google Health activity and fitness access is required")
        if not credentials.refresh_token:
            raise ValueError("Google did not return a refresh token. Please register again.")

        service = build("health", "v4", credentials=credentials, discoveryServiceUrl=cls.api_endpoint)
        try:
            service.users().getIdentity(name="users/me/identity").execute()
        except HttpError as error:
            if error.resp.status == 400 and b"ACCOUNT_NOT_LINKED" in error.content:
                raise ValueError(
                    "Your Google Account is not linked to Google Health yet. Open the Google Health app, "
                    "link or migrate your Fitbit account, then register again."
                ) from error
            raise
        return credentials

    @classmethod
    async def store_auth_token(cls, user_id, guild_id, code):
        flow_key = (str(user_id), str(guild_id))
        flow = cls.pending_flows.get(flow_key)
        if not flow:
            raise ValueError("Your registration session expired. Run /fitbot register and try again.")
        credentials = await asyncio.to_thread(cls._exchange_code, code, flow)
        cls.pending_flows.pop(flow_key, None)
        expires_at = credentials.expiry
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        auth = ThirdPartyAuth(
            user_id=str(user_id),
            provider=cls.provider,
            guild_id=str(guild_id),
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            scope=" ".join(credentials.granted_scopes or cls.config.scope),
            expires_at=expires_at,
        )

        async for session in get_session():
            legacy_stmt = select(ThirdPartyAuth).where(
                ThirdPartyAuth.user_id == str(user_id),
                ThirdPartyAuth.provider == FitbotConfig.legacy_provider,
                ThirdPartyAuth.guild_id == str(guild_id),
            )
            legacy_result = await session.exec(legacy_stmt)
            legacy_auth = legacy_result.first()
            if legacy_auth:
                await session.delete(legacy_auth)

            existing_stmt = select(ThirdPartyAuth).where(
                ThirdPartyAuth.user_id == str(user_id),
                ThirdPartyAuth.provider == cls.provider,
                ThirdPartyAuth.guild_id == str(guild_id),
            )
            existing_result = await session.exec(existing_stmt)
            existing_auth = existing_result.first()
            if existing_auth:
                existing_auth.access_token = auth.access_token
                existing_auth.refresh_token = auth.refresh_token
                existing_auth.scope = auth.scope
                existing_auth.expires_at = auth.expires_at
                auth = existing_auth
            else:
                session.add(auth)
            await session.commit()
            await session.refresh(auth)
            return auth

    @classmethod
    async def disconnect_user(cls, user_id, guild_id):
        async for session in get_session():
            stmt = select(ThirdPartyAuth).where(
                ThirdPartyAuth.user_id == str(user_id),
                ThirdPartyAuth.provider.in_([cls.provider, FitbotConfig.legacy_provider]),
                ThirdPartyAuth.guild_id == str(guild_id),
            )
            result = await session.exec(stmt)
            for auth in result.all():
                await session.delete(auth)
            await session.commit()

    @classmethod
    async def get_user_auth(cls, user_id, guild_id):
        async for session in get_session():
            stmt = select(ThirdPartyAuth).where(
                ThirdPartyAuth.user_id == str(user_id),
                ThirdPartyAuth.provider == cls.provider,
                ThirdPartyAuth.guild_id == str(guild_id),
            )
            result = await session.exec(stmt)
            auth = result.first()

        if not auth:
            raise LookupError("User Google Health credentials not found")
        return auth

    @classmethod
    def _get_credentials(cls, auth):
        expiry = auth.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        credentials = google.oauth2.credentials.Credentials(
            token=auth.access_token,
            refresh_token=auth.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=cls.config.client_id,
            client_secret=cls.config.client_secret,
            scopes=auth.scope.split(),
        )
        credentials.expiry = expiry.astimezone(UTC).replace(tzinfo=None)
        if credentials.expired:
            credentials.refresh(google.auth.transport.requests.Request())
        return credentials

    @classmethod
    async def _build_health_service(cls, auth):
        credentials = await asyncio.to_thread(cls._get_credentials, auth)
        if credentials.token != auth.access_token or credentials.refresh_token != auth.refresh_token:
            auth.access_token = credentials.token
            auth.refresh_token = credentials.refresh_token
            auth.expires_at = credentials.expiry.replace(tzinfo=UTC)
            async for session in get_session():
                await session.merge(auth)
                await session.commit()
        return await asyncio.to_thread(
            build,
            "health",
            "v4",
            credentials=credentials,
            discoveryServiceUrl=cls.api_endpoint,
        )

    @classmethod
    async def get_guild_weekly_stats(cls, guild_id):
        user_auths = []
        async for session in get_session():
            stmt = select(ThirdPartyAuth).where(
                ThirdPartyAuth.provider == cls.provider,
                ThirdPartyAuth.guild_id == str(guild_id),
            )
            result = await session.exec(stmt)
            user_auths = result.all()

        user_stats = []
        for auth in user_auths:
            try:
                stats = await cls.get_user_weekly_stats(auth)
                user_stats.append(stats)
            except Exception:
                logger.exception("Error fetching stats for user %s", auth.user_id)

        return GuildWeeklyStats(user_stats)

    @classmethod
    async def get_user_weekly_stats(cls, auth):
        service = await cls._build_health_service(auth)
        end_date = date.today() + timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        days = [(start_date + timedelta(days=offset)).isoformat() for offset in range(7)]

        rollups = await asyncio.to_thread(cls._get_weekly_rollups, service, start_date, end_date)
        steps, distances, active_minutes = rollups
        steps_by_day = cls._rollup_values(steps, "steps", "countSum")
        distance_by_day = cls._rollup_values(distances, "distance", "millimetersSum")
        active_by_day = cls._active_minutes_by_day(active_minutes)

        return UserWeeklyStats(
            user_id=auth.user_id,
            fairly_active=[{"dateTime": day, "value": active_by_day.get(day, {}).get("MODERATE", 0)} for day in days],
            very_active=[{"dateTime": day, "value": active_by_day.get(day, {}).get("VIGOROUS", 0)} for day in days],
            steps=[{"dateTime": day, "value": steps_by_day.get(day, 0)} for day in days],
            distance=[{"dateTime": day, "value": float(distance_by_day.get(day, 0)) / 1_000_000} for day in days],
        )

    @classmethod
    def _get_weekly_rollups(cls, service, start_date, end_date):
        results = []
        for data_type in ("steps", "distance", "active-minutes"):
            response = (
                service.users()
                .dataTypes()
                .dataPoints()
                .dailyRollUp(
                    parent=f"users/me/dataTypes/{data_type}",
                    body={
                        "range": {
                            "start": {"date": cls._civil_date(start_date)},
                            "end": {"date": cls._civil_date(end_date)},
                        },
                        "windowSizeDays": 1,
                    },
                )
                .execute()
            )
            results.append(response.get("rollupDataPoints", []))
        return results

    @staticmethod
    def _civil_date(day):
        return {"year": day.year, "month": day.month, "day": day.day}

    @staticmethod
    def _rollup_values(points, value_field, value_key):
        values = {}
        for point in points:
            civil_day = point["civilStartTime"]["date"]
            day = date(civil_day["year"], civil_day["month"], civil_day["day"]).isoformat()
            values[day] = point.get(value_field, {}).get(value_key, 0)
        return values

    @staticmethod
    def _active_minutes_by_day(points):
        values = {}
        for point in points:
            civil_day = point["civilStartTime"]["date"]
            day = date(civil_day["year"], civil_day["month"], civil_day["day"]).isoformat()
            levels = point.get("activeMinutes", {}).get("activeMinutesRollupByActivityLevel", [])
            values[day] = {level["activityLevel"]: int(level.get("activeMinutesSum", 0)) for level in levels}
        return values

    @classmethod
    async def get_registered_guild_ids(cls):
        async for session in get_session():
            stmt = select(ThirdPartyAuth.guild_id).where(ThirdPartyAuth.provider == cls.provider).distinct()
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
                if getattr(user_stat, metric) is not None
            ],
            key=lambda leaderboard_entry: leaderboard_entry.score,
            reverse=True,
        )

    @property
    def user_ids(self):
        return [user.user_id for user in self.user_stats]

    @property
    def steps_df(self):
        return self._metric_df("steps")

    @cached_property
    def distance_df(self):
        return self._metric_df("distance")

    def _metric_df(self, metric):
        data = {}
        for user_stat in self.user_stats:
            metric_data = getattr(user_stat, metric)
            series = pd.Series(metric_data, index=user_stat.metric_days[-len(metric_data) :])
            data[user_stat.user_id] = series
        return pd.DataFrame(data)


class UserWeeklyStats:
    def __init__(
        self,
        user_id,
        fairly_active,
        very_active,
        steps,
        distance,
    ):
        self.user_id = user_id
        self._fairly_active_min_data = fairly_active
        self._very_active_min_data = very_active
        self._steps_data = steps
        self._distance_data = distance

    @staticmethod
    def _time_series_values(series, data_type):
        return [data_type(day["value"]) for day in series]

    @property
    def metric_days(self):
        return [datetime.strptime(day["dateTime"], "%Y-%m-%d") for day in self._steps_data]

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
        return self.total_fairly_active_minutes + self.total_very_active_minutes
