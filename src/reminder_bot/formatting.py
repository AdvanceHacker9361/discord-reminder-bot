from __future__ import annotations

from datetime import tzinfo

from .models import Reminder


def _format_local(value, timezone: tzinfo) -> str:
    return value.astimezone(timezone).strftime("%Y-%m-%d %H:%M")


def format_reminder_line(reminder: Reminder, timezone: tzinfo) -> str:
    assignee = f" <@{reminder.assignee_user_id}>" if reminder.assignee_user_id else ""
    due = _format_local(reminder.due_at, timezone)
    return f"`#{reminder.id}` {reminder.title}{assignee} - due {due} ({reminder.status})"


def format_notification(reminder: Reminder, timezone: tzinfo) -> str:
    due = _format_local(reminder.due_at, timezone)
    assignee = f"\n担当: <@{reminder.assignee_user_id}>" if reminder.assignee_user_id else ""
    creator = f"\n作成者: <@{reminder.creator_user_id}>"
    description = f"\n詳細: {reminder.description}" if reminder.description else ""
    return (
        "**工程リマインダー**\n"
        f"工程: {reminder.title}"
        f"{assignee}"
        f"{creator}"
        f"\n期限: {due}"
        f"{description}"
        f"\nID: `#{reminder.id}`"
    )


def format_reminder_detail(reminder: Reminder, timezone: tzinfo) -> str:
    assignee = f"<@{reminder.assignee_user_id}>" if reminder.assignee_user_id else "未設定"
    lines = [
        f"**工程リマインダー `#{reminder.id}`**",
        f"工程: {reminder.title}",
        f"状態: {reminder.status}",
        f"担当: {assignee}",
        f"作成者: <@{reminder.creator_user_id}>",
        f"通知先: <#{reminder.channel_id}>",
        f"通知日時: {_format_local(reminder.remind_at, timezone)}",
        f"期限: {_format_local(reminder.due_at, timezone)}",
    ]
    if reminder.description:
        lines.append(f"詳細: {reminder.description}")
    if reminder.notified_at is not None:
        lines.append(f"通知済み: {_format_local(reminder.notified_at, timezone)}")
    if reminder.last_notification_error:
        lines.append(f"最終通知エラー: {reminder.last_notification_error}")
    return "\n".join(lines)
