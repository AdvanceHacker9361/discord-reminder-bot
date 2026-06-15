from __future__ import annotations

import asyncio
import logging

import truststore

truststore.inject_into_ssl()

import discord
from discord.ext import commands

from .config import Settings, load_settings
from .reminder_service import ReminderService
from .scheduler import ReminderScheduler


class ReminderBot(commands.Bot):
    def __init__(self, settings: Settings, service: ReminderService):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        self.reminder_service = service

    async def setup_hook(self) -> None:
        await self.load_extension("reminder_bot.commands.reminder")
        await self.add_cog(
            ReminderScheduler(
                self,
                self.reminder_service,
                self.settings.poll_interval_seconds,
            )
        )

        if self.settings.development_guild_id is not None:
            guild = discord.Object(id=self.settings.development_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    service = ReminderService(settings.database_path)
    bot = ReminderBot(settings, service)
    await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())
