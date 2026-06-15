from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from reminder_bot.reminder_service import ReminderService


class ReminderServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "reminders.sqlite3"
        self.service = ReminderService(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_list_pending_reminder(self) -> None:
        due_at = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)

        created = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            assignee_user_id=4,
            title="Review draft",
            due_at=due_at,
        )

        reminders = self.service.list_reminders(1)
        self.assertEqual([created.id], [reminder.id for reminder in reminders])
        self.assertEqual("Review draft", reminders[0].title)

    def test_create_trims_title_and_description(self) -> None:
        created = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="  Review draft  ",
            description="  Check it.  ",
            due_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        )

        self.assertEqual("Review draft", created.title)
        self.assertEqual("Check it.", created.description)

    def test_rejects_blank_title(self) -> None:
        with self.assertRaises(ValueError):
            self.service.create_reminder(
                guild_id=1,
                channel_id=2,
                creator_user_id=3,
                title=" ",
                due_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
            )

    def test_done_reminders_are_hidden_by_default(self) -> None:
        reminder = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="Publish",
            due_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        )

        self.service.mark_done(1, reminder.id, completed_by_user_id=5)

        self.assertEqual([], self.service.list_reminders(1))
        self.assertEqual(["done"], [item.status for item in self.service.list_reminders(1, include_done=True)])

    def test_deleted_reminders_are_hidden_from_lists(self) -> None:
        reminder = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="Remove",
            due_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        )

        deleted = self.service.delete_reminder(1, reminder.id)

        self.assertEqual("deleted", deleted.status)
        self.assertEqual([], self.service.list_reminders(1, include_done=True))

    def test_due_for_notification_returns_unnotified_pending_items(self) -> None:
        now = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
        due_reminder = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="Due",
            due_at=now + timedelta(hours=1),
            remind_at=now - timedelta(minutes=1),
        )
        self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="Later",
            due_at=now + timedelta(hours=2),
            remind_at=now + timedelta(minutes=10),
        )

        reminders = self.service.due_for_notification(now=now)

        self.assertEqual([due_reminder.id], [reminder.id for reminder in reminders])

    def test_mark_notified_excludes_reminder_from_future_notifications(self) -> None:
        now = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
        reminder = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="Notify once",
            due_at=now,
            remind_at=now,
        )

        self.service.mark_notified(reminder.id, notified_at=now)

        self.assertEqual([], self.service.due_for_notification(now=now))

    def test_failed_notification_is_recorded_and_temporarily_skipped(self) -> None:
        now = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
        reminder = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="Retry later",
            due_at=now,
            remind_at=now,
        )

        self.service.mark_notification_failed(reminder.id, "Missing permissions", attempted_at=now)

        self.assertEqual([], self.service.due_for_notification(now=now + timedelta(minutes=4)))
        retried = self.service.due_for_notification(now=now + timedelta(minutes=5))
        self.assertEqual([reminder.id], [item.id for item in retried])
        current = self.service.get_reminder(1, reminder.id)
        self.assertEqual(1, current.notification_attempts)
        self.assertEqual("Missing permissions", current.last_notification_error)

    def test_claimed_notification_is_temporarily_skipped_by_other_pollers(self) -> None:
        now = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
        reminder = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="Claim once",
            due_at=now,
            remind_at=now,
        )

        claimed = self.service.claim_due_for_notification(now=now)

        self.assertEqual([reminder.id], [item.id for item in claimed])
        self.assertEqual([], self.service.claim_due_for_notification(now=now + timedelta(seconds=30)))
        reclaimed = self.service.claim_due_for_notification(now=now + timedelta(minutes=2))
        self.assertEqual([reminder.id], [item.id for item in reclaimed])

    def test_mark_notified_does_not_update_done_reminder(self) -> None:
        now = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
        reminder = self.service.create_reminder(
            guild_id=1,
            channel_id=2,
            creator_user_id=3,
            title="Already done",
            due_at=now,
            remind_at=now,
        )

        self.service.mark_done(1, reminder.id, completed_by_user_id=5)
        self.service.mark_notified(reminder.id, notified_at=now)

        current = self.service.get_reminder(1, reminder.id)
        self.assertIsNone(current.notified_at)

    def test_rejects_remind_at_after_due_at(self) -> None:
        due_at = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)

        with self.assertRaises(ValueError):
            self.service.create_reminder(
                guild_id=1,
                channel_id=2,
                creator_user_id=3,
                title="Invalid",
                due_at=due_at,
                remind_at=due_at + timedelta(minutes=1),
            )


if __name__ == "__main__":
    unittest.main()
