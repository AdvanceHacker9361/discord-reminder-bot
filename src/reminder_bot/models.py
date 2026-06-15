from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3


@dataclass(frozen=True)
class Reminder:
    id: int
    guild_id: int
    channel_id: int
    creator_user_id: int
    assignee_user_id: int | None
    title: str
    description: str
    due_at: datetime
    remind_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    completed_by_user_id: int | None
    notified_at: datetime | None
    notification_attempts: int
    last_notification_attempt_at: datetime | None
    last_notification_error: str | None
    notification_claimed_until: datetime | None


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def reminder_from_row(row: sqlite3.Row) -> Reminder:
    return Reminder(
        id=row["id"],
        guild_id=row["guild_id"],
        channel_id=row["channel_id"],
        creator_user_id=row["creator_user_id"],
        assignee_user_id=row["assignee_user_id"],
        title=row["title"],
        description=row["description"],
        due_at=parse_datetime(row["due_at"]),
        remind_at=parse_datetime(row["remind_at"]),
        status=row["status"],
        created_at=parse_datetime(row["created_at"]),
        updated_at=parse_datetime(row["updated_at"]),
        completed_at=parse_datetime(row["completed_at"]),
        completed_by_user_id=row["completed_by_user_id"],
        notified_at=parse_datetime(row["notified_at"]),
        notification_attempts=row["notification_attempts"],
        last_notification_attempt_at=parse_datetime(row["last_notification_attempt_at"]),
        last_notification_error=row["last_notification_error"],
        notification_claimed_until=parse_datetime(row["notification_claimed_until"]),
    )
