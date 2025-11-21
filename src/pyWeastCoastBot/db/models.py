from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, UniqueConstraint


class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    guild_id: str
    channel_id: str
    message_id: str
    message: Optional[str] = Field(default=None)
    remind_time: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

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
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
