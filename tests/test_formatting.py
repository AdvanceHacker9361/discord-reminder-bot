from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
import unittest

from reminder_bot.formatting import format_notification, format_reminder_detail, format_reminder_line
from reminder_bot.models import Reminder


class FormattingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.timezone = timezone(timedelta(hours=9), "JST")
        self.reminder = Reminder(
            id=7,
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            assignee_user_id=4,
            title="Review draft",
            description="Check the final copy.",
            due_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
            remind_at=datetime(2026, 6, 20, 8, 30, tzinfo=UTC),
            status="pending",
            created_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
            completed_at=None,
            completed_by_user_id=None,
            notified_at=None,
            notification_attempts=0,
            last_notification_attempt_at=None,
            last_notification_error=None,
            notification_claimed_until=None,
        )

    def test_format_reminder_line(self) -> None:
        line = format_reminder_line(self.reminder, self.timezone)

        self.assertIn("`#7` Review draft", line)
        self.assertIn("<@4>", line)
        self.assertIn("2026-06-20 18:00", line)

    def test_format_notification_includes_creator_and_assignee(self) -> None:
        message = format_notification(self.reminder, self.timezone)

        self.assertIn("担当: <@4>", message)
        self.assertIn("作成者: <@3>", message)
        self.assertIn("期限: 2026-06-20 18:00", message)

    def test_format_reminder_detail(self) -> None:
        detail = format_reminder_detail(self.reminder, self.timezone)

        self.assertIn("**工程リマインダー `#7`**", detail)
        self.assertIn("通知先: <#2>", detail)
        self.assertIn("通知日時: 2026-06-20 17:30", detail)
        self.assertIn("詳細: Check the final copy.", detail)


if __name__ == "__main__":
    unittest.main()

