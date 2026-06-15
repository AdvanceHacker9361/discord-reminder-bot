from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from .database import init_db, open_database
from .models import Reminder, reminder_from_row


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime values must be timezone-aware")
    return value.astimezone(UTC)


def _serialize(value: datetime) -> str:
    return _to_utc(value).isoformat()


def _retry_cutoff(current: datetime, retry_after_seconds: int) -> datetime:
    return datetime.fromtimestamp(current.timestamp() - retry_after_seconds, tz=UTC)


class ReminderService:
    notification_retry_after_seconds = 300
    notification_claim_seconds = 120

    def __init__(self, database_path: Path):
        self.database_path = database_path
        init_db(database_path)

    def create_reminder(
        self,
        *,
        guild_id: int,
        channel_id: int,
        creator_user_id: int,
        title: str,
        due_at: datetime,
        description: str = "",
        remind_at: datetime | None = None,
        assignee_user_id: int | None = None,
    ) -> Reminder:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("title is required")

        effective_remind_at = remind_at or due_at
        if _to_utc(effective_remind_at) > _to_utc(due_at):
            raise ValueError("remind_at must be before or equal to due_at")

        now = _now_utc()
        with open_database(self.database_path) as connection:
            existing = connection.execute(
                """
                SELECT * FROM reminders
                WHERE guild_id = ?
                  AND channel_id = ?
                  AND creator_user_id = ?
                  AND title = ?
                  AND due_at = ?
                  AND remind_at = ?
                  AND status = 'pending'
                ORDER BY id ASC
                LIMIT 1
                """,
                (
                    guild_id,
                    channel_id,
                    creator_user_id,
                    clean_title,
                    _serialize(due_at),
                    _serialize(effective_remind_at),
                ),
            ).fetchone()
            if existing is not None:
                raise ValueError(f"duplicate reminder already exists as #{existing['id']}")

            cursor = connection.execute(
                """
                INSERT INTO reminders (
                    guild_id, channel_id, creator_user_id, assignee_user_id,
                    title, description, due_at, remind_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    channel_id,
                    creator_user_id,
                    assignee_user_id,
                    clean_title,
                    description.strip(),
                    _serialize(due_at),
                    _serialize(effective_remind_at),
                    _serialize(now),
                    _serialize(now),
                ),
            )
            row = connection.execute(
                "SELECT * FROM reminders WHERE guild_id = ? AND id = ?",
                (guild_id, cursor.lastrowid),
            ).fetchone()
            return reminder_from_row(row)

    def get_reminder(self, guild_id: int, reminder_id: int) -> Reminder:
        with open_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM reminders WHERE guild_id = ? AND id = ?",
                (guild_id, reminder_id),
            ).fetchone()
        if row is None:
            raise LookupError(f"reminder {reminder_id} was not found")
        return reminder_from_row(row)

    def list_reminders(self, guild_id: int, *, include_done: bool = False) -> list[Reminder]:
        statuses = ("pending", "done") if include_done else ("pending",)
        placeholders = ", ".join("?" for _ in statuses)
        with open_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM reminders
                WHERE guild_id = ? AND status IN ({placeholders})
                ORDER BY due_at ASC, id ASC
                """,
                (guild_id, *statuses),
            ).fetchall()
        return [reminder_from_row(row) for row in rows]

    def mark_done(self, guild_id: int, reminder_id: int, completed_by_user_id: int) -> Reminder:
        now = _now_utc()
        with open_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE reminders
                SET status = 'done',
                    completed_at = ?,
                    completed_by_user_id = ?,
                    updated_at = ?
                WHERE guild_id = ? AND id = ? AND status = 'pending'
                """,
                (_serialize(now), completed_by_user_id, _serialize(now), guild_id, reminder_id),
            )
            if cursor.rowcount == 0:
                raise LookupError(f"pending reminder {reminder_id} was not found")
        return self.get_reminder(guild_id, reminder_id)

    def delete_reminder(self, guild_id: int, reminder_id: int) -> Reminder:
        now = _now_utc()
        with open_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE reminders
                SET status = 'deleted', updated_at = ?
                WHERE guild_id = ? AND id = ? AND status != 'deleted'
                """,
                (_serialize(now), guild_id, reminder_id),
            )
            if cursor.rowcount == 0:
                raise LookupError(f"reminder {reminder_id} was not found")
        return self.get_reminder(guild_id, reminder_id)

    def due_for_notification(self, *, now: datetime | None = None, limit: int = 20) -> list[Reminder]:
        current = now or _now_utc()
        with open_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM reminders
                WHERE status = 'pending'
                  AND notified_at IS NULL
                  AND remind_at <= ?
                  AND (
                      last_notification_attempt_at IS NULL
                      OR last_notification_attempt_at <= ?
                  )
                  AND (
                      notification_claimed_until IS NULL
                      OR notification_claimed_until <= ?
                  )
                ORDER BY remind_at ASC, id ASC
                LIMIT ?
                """,
                (
                    _serialize(current),
                    _serialize(_retry_cutoff(current, self.notification_retry_after_seconds)),
                    _serialize(current),
                    limit,
                ),
            ).fetchall()
        return [reminder_from_row(row) for row in rows]

    def claim_due_for_notification(
        self,
        *,
        now: datetime | None = None,
        limit: int = 20,
    ) -> list[Reminder]:
        current = now or _now_utc()
        claimed_until = current + timedelta(seconds=self.notification_claim_seconds)
        with open_database(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """
                SELECT * FROM reminders
                WHERE status = 'pending'
                  AND notified_at IS NULL
                  AND remind_at <= ?
                  AND (
                      last_notification_attempt_at IS NULL
                      OR last_notification_attempt_at <= ?
                  )
                  AND (
                      notification_claimed_until IS NULL
                      OR notification_claimed_until <= ?
                  )
                ORDER BY remind_at ASC, id ASC
                LIMIT ?
                """,
                (
                    _serialize(current),
                    _serialize(_retry_cutoff(current, self.notification_retry_after_seconds)),
                    _serialize(current),
                    limit,
                ),
            ).fetchall()
            if not rows:
                return []

            reminder_ids = [row["id"] for row in rows]
            placeholders = ", ".join("?" for _ in reminder_ids)
            connection.execute(
                f"""
                UPDATE reminders
                SET notification_claimed_until = ?, updated_at = ?
                WHERE id IN ({placeholders})
                  AND status = 'pending'
                  AND notified_at IS NULL
                """,
                (_serialize(claimed_until), _serialize(current), *reminder_ids),
            )

            rows = connection.execute(
                f"SELECT * FROM reminders WHERE id IN ({placeholders}) ORDER BY remind_at ASC, id ASC",
                reminder_ids,
            ).fetchall()
        return [reminder_from_row(row) for row in rows]

    def mark_notified(self, reminder_id: int, *, notified_at: datetime | None = None) -> None:
        now = notified_at or _now_utc()
        with open_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE reminders
                SET notified_at = ?,
                    last_notification_attempt_at = ?,
                    last_notification_error = NULL,
                    notification_claimed_until = NULL,
                    updated_at = ?
                WHERE id = ? AND status = 'pending' AND notified_at IS NULL
                """,
                (_serialize(now), _serialize(now), _serialize(now), reminder_id),
            )

    def mark_notification_failed(
        self,
        reminder_id: int,
        error: str,
        *,
        attempted_at: datetime | None = None,
    ) -> None:
        now = attempted_at or _now_utc()
        with open_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE reminders
                SET notification_attempts = notification_attempts + 1,
                    last_notification_attempt_at = ?,
                    last_notification_error = ?,
                    notification_claimed_until = NULL,
                    updated_at = ?
                WHERE id = ? AND status = 'pending' AND notified_at IS NULL
                """,
                (_serialize(now), error[:500], _serialize(now), reminder_id),
            )
