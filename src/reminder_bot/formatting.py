from __future__ import annotations

from zoneinfo import ZoneInfo

from .models import Reminder


def format_reminder_line(reminder: Reminder, timezone: ZoneInfo) -> str:
    assignee = f" <@{reminder.assignee_user_id}>" if reminder.assignee_user_id else ""
    due = reminder.due_at.astimezone(timezone).strftime("%Y-%m-%d %H:%M")
    return f"`#{reminder.id}` {reminder.title}{assignee} - due {due} ({reminder.status})"


def format_notification(reminder: Reminder, timezone: ZoneInfo) -> str:
    due = reminder.due_at.astimezone(timezone).strftime("%Y-%m-%d %H:%M")
    assignee = f"\n担当: <@{reminder.assignee_user_id}>" if reminder.assignee_user_id else ""
    description = f"\n詳細: {reminder.description}" if reminder.description else ""
    return (
        "**工程リマインダー**\n"
        f"工程: {reminder.title}"
        f"{assignee}"
        f"\n期限: {due}"
        f"{description}"
        f"\nID: `#{reminder.id}`"
    )

