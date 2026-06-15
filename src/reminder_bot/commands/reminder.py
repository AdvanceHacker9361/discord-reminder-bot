from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from ..formatting import format_reminder_line
from ..reminder_service import ReminderService
from ..time_parser import parse_local_datetime


class ReminderCog(commands.Cog):
    def __init__(self, bot: commands.Bot, service: ReminderService):
        self.bot = bot
        self.service = service

    reminder = app_commands.Group(name="reminder", description="工程リマインダーを管理します")

    def _can_delete(self, interaction: discord.Interaction, creator_user_id: int) -> bool:
        if interaction.user.id == creator_user_id:
            return True
        permissions = getattr(interaction.user, "guild_permissions", None)
        return bool(permissions and permissions.manage_messages)

    @reminder.command(name="add", description="工程リマインダーを追加します")
    @app_commands.describe(
        title="工程名",
        due_at="期限。例: 2026-06-20 18:00",
        description="工程の補足説明",
        assignee="担当者",
        remind_at="通知日時。省略時は期限と同じです",
        channel="通知先チャンネル。省略時は現在のチャンネルです",
    )
    async def add(
        self,
        interaction: discord.Interaction,
        title: str,
        due_at: str,
        description: str = "",
        assignee: discord.Member | None = None,
        remind_at: str | None = None,
        channel: discord.TextChannel | None = None,
    ) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return

        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message("テキストチャンネルを指定してください。", ephemeral=True)
            return

        guild = interaction.guild
        bot_member = guild.me if guild is not None else None
        if bot_member is None or not target_channel.permissions_for(bot_member).send_messages:
            await interaction.response.send_message("そのチャンネルへBotが投稿できません。", ephemeral=True)
            return

        try:
            due = parse_local_datetime(due_at, self.bot.settings.timezone)
            remind = parse_local_datetime(remind_at, self.bot.settings.timezone) if remind_at else None
            reminder = self.service.create_reminder(
                guild_id=interaction.guild_id,
                channel_id=target_channel.id,
                creator_user_id=interaction.user.id,
                assignee_user_id=assignee.id if assignee else None,
                title=title,
                description=description,
                due_at=due,
                remind_at=remind,
            )
        except ValueError as exc:
            await interaction.response.send_message(f"入力を確認してください: {exc}", ephemeral=True)
            return

        await interaction.response.send_message(
            f"登録しました: {format_reminder_line(reminder, self.bot.settings.timezone)}",
            ephemeral=True,
        )

    @reminder.command(name="list", description="工程リマインダー一覧を表示します")
    @app_commands.describe(include_done="完了済みも表示します")
    async def list(self, interaction: discord.Interaction, include_done: bool = False) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return

        reminders = self.service.list_reminders(interaction.guild_id, include_done=include_done)
        if not reminders:
            await interaction.response.send_message("リマインダーはありません。", ephemeral=True)
            return

        lines = [format_reminder_line(reminder, self.bot.settings.timezone) for reminder in reminders[:20]]
        suffix = "\n..." if len(reminders) > 20 else ""
        await interaction.response.send_message("\n".join(lines) + suffix, ephemeral=True)

    @reminder.command(name="done", description="工程リマインダーを完了にします")
    @app_commands.describe(reminder_id="完了するリマインダーID")
    async def done(self, interaction: discord.Interaction, reminder_id: int) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return

        try:
            reminder = self.service.mark_done(interaction.guild_id, reminder_id, interaction.user.id)
        except LookupError:
            await interaction.response.send_message("未完了のリマインダーが見つかりません。", ephemeral=True)
            return

        await interaction.response.send_message(
            f"完了にしました: {format_reminder_line(reminder, self.bot.settings.timezone)}",
            ephemeral=True,
        )

    @reminder.command(name="delete", description="工程リマインダーを削除します")
    @app_commands.describe(reminder_id="削除するリマインダーID")
    async def delete(self, interaction: discord.Interaction, reminder_id: int) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return

        try:
            existing = self.service.get_reminder(interaction.guild_id, reminder_id)
        except LookupError:
            await interaction.response.send_message("リマインダーが見つかりません。", ephemeral=True)
            return

        if not self._can_delete(interaction, existing.creator_user_id):
            await interaction.response.send_message("削除できるのは作成者またはメッセージ管理権限のあるメンバーです。", ephemeral=True)
            return

        reminder = self.service.delete_reminder(interaction.guild_id, reminder_id)
        await interaction.response.send_message(
            f"削除しました: `#{reminder.id}` {reminder.title}",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReminderCog(bot, bot.reminder_service))
