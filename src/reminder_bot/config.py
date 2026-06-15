from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is optional for tests
    load_dotenv = None


@dataclass(frozen=True)
class Settings:
    discord_token: str
    database_path: Path
    timezone: ZoneInfo
    poll_interval_seconds: int
    development_guild_id: int | None


def load_settings() -> Settings:
    if load_dotenv is not None:
        load_dotenv()

    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN is required. Copy .env.example to .env and set it.")

    guild_id_raw = os.getenv("DISCORD_GUILD_ID", "").strip()
    return Settings(
        discord_token=token,
        database_path=Path(os.getenv("DATABASE_PATH", "data/reminders.sqlite3")),
        timezone=ZoneInfo(os.getenv("TIMEZONE", "Asia/Tokyo")),
        poll_interval_seconds=int(os.getenv("REMINDER_POLL_INTERVAL_SECONDS", "30")),
        development_guild_id=int(guild_id_raw) if guild_id_raw else None,
    )

