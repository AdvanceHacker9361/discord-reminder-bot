from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    creator_user_id INTEGER NOT NULL,
    assignee_user_id INTEGER,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    due_at TEXT NOT NULL,
    remind_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done', 'deleted')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    completed_by_user_id INTEGER,
    notified_at TEXT,
    notification_attempts INTEGER NOT NULL DEFAULT 0,
    last_notification_attempt_at TEXT,
    last_notification_error TEXT,
    notification_claimed_until TEXT
);

CREATE INDEX IF NOT EXISTS idx_reminders_guild_status_due
    ON reminders (guild_id, status, due_at);

CREATE INDEX IF NOT EXISTS idx_reminders_notify
    ON reminders (status, notified_at, remind_at);
"""


MIGRATIONS = {
    "notification_attempts": "ALTER TABLE reminders ADD COLUMN notification_attempts INTEGER NOT NULL DEFAULT 0",
    "last_notification_attempt_at": "ALTER TABLE reminders ADD COLUMN last_notification_attempt_at TEXT",
    "last_notification_error": "ALTER TABLE reminders ADD COLUMN last_notification_error TEXT",
    "notification_claimed_until": "ALTER TABLE reminders ADD COLUMN notification_claimed_until TEXT",
}


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


@contextmanager
def open_database(database_path: Path):
    connection = connect(database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db(database_path: Path) -> None:
    with open_database(database_path) as connection:
        connection.executescript(SCHEMA)
        existing_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(reminders)").fetchall()
        }
        for column_name, statement in MIGRATIONS.items():
            if column_name not in existing_columns:
                connection.execute(statement)
