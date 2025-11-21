from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    channel_id: str
    message_id: str
    message: Optional[str] = Field(default=None)
    remind_time: datetime

    def __str__(self) -> str:
        return f"Reminder({self.remind_time})"


class ThirdPartyAuth(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "provider", "guild_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    provider: str
    guild_id: str
    access_token: str
    refresh_token: str
    scope: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
