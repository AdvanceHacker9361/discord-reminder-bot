from __future__ import annotations

import logging

import discord
from discord.ext import commands, tasks

from .formatting import format_notification
from .reminder_service import ReminderService

logger = logging.getLogger(__name__)


class ReminderScheduler(commands.Cog):
    def __init__(self, bot: commands.Bot, service: ReminderService, poll_interval_seconds: int):
        self.bot = bot
        self.service = service
        self.poll_notifications.change_interval(seconds=poll_interval_seconds)

    async def cog_load(self) -> None:
        self.poll_notifications.start()

    async def cog_unload(self) -> None:
        self.poll_notifications.cancel()

    @tasks.loop(seconds=30)
    async def poll_notifications(self) -> None:
        for reminder in self.service.claim_due_for_notification():
            channel = self.bot.get_channel(reminder.channel_id)
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(reminder.channel_id)
                except discord.DiscordException as exc:
                    logger.exception("Failed to fetch channel %s", reminder.channel_id)
                    self.service.mark_notification_failed(reminder.id, str(exc))
                    continue

            if not isinstance(channel, discord.abc.Messageable):
                logger.warning("Channel %s is not messageable", reminder.channel_id)
                self.service.mark_notification_failed(reminder.id, "Channel is not messageable")
                continue

            try:
                allowed_mentions = discord.AllowedMentions(
                    everyone=False,
                    users=[discord.Object(id=reminder.assignee_user_id)] if reminder.assignee_user_id else False,
                    roles=False,
                    replied_user=False,
                )
                await channel.send(
                    format_notification(reminder, self.bot.settings.timezone),
                    allowed_mentions=allowed_mentions,
                )
            except discord.DiscordException as exc:
                logger.exception("Failed to send reminder %s", reminder.id)
                self.service.mark_notification_failed(reminder.id, str(exc))
                continue

            self.service.mark_notified(reminder.id)

    @poll_notifications.before_loop
    async def before_poll_notifications(self) -> None:
        await self.bot.wait_until_ready()

    @poll_notifications.error
    async def on_poll_notifications_error(self, error: Exception) -> None:
        logger.exception("Reminder notification loop stopped unexpectedly", exc_info=error)
