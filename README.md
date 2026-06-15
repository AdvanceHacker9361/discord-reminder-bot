# Discord Reminder Bot

Discord server bot for posting project-process reminders into channels.

## MVP scope

- Register reminders with `/reminder add`
- List pending reminders with `/reminder list`
- Mark reminders as done with `/reminder done`
- Delete reminders with `/reminder delete`
- Post a channel notification when a reminder reaches its notify time
- Persist reminders in SQLite across bot restarts

## Setup

1. Create a Discord application in the Discord Developer Portal.
2. Open the application's Bot page, create a bot, and copy its token.
3. Privileged Gateway Intents are not required for this MVP. Message Content,
   Server Members, and Presence intents can stay off.
4. In Discord, enable Developer Mode and copy your test server ID if you want
   fast development command syncing.
5. Open OAuth2 URL Generator and select:
   - `bot`
   - `applications.commands`
6. Select bot permissions:
   - View Channels
   - Send Messages
   - Embed Links
7. Open the generated URL and invite the bot to your test server.
8. Copy `.env.example` to `.env`.
9. Set `DISCORD_TOKEN` in `.env`.
10. During development, set `DISCORD_GUILD_ID` to your test server ID.
11. Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

12. Run the bot:

```powershell
python -m reminder_bot.bot
```

For local development, set `DISCORD_GUILD_ID` to your test server ID so slash
commands sync quickly to that server.

If you install with `pip install -r requirements.txt` instead of `pip install -e .`,
set `PYTHONPATH` before running commands:

```powershell
$env:PYTHONPATH='src'
python -m reminder_bot.bot
```

## Bot permissions

Invite the bot with these capabilities:

- `bot`
- `applications.commands`
- Send Messages
- View Channels

The OAuth2 permission value for View Channels and Send Messages is `3072`.
The bot must have these permissions in each notification target channel.

## Commands

```text
/reminder add title due_at description assignee remind_at channel
/reminder list include_done
/reminder show reminder_id
/reminder done reminder_id
/reminder delete reminder_id
```

Examples:

```text
/reminder add title:"資料レビュー" due_at:"2h" assignee:@tanaka
/reminder add title:"公開前チェック" due_at:"2026-06-20 18:00" remind_at:"2026-06-20 17:30" channel:#作業通知
/reminder list
/reminder show reminder_id:7
/reminder done reminder_id:7
/reminder delete reminder_id:7
```

When `remind_at` is omitted, the bot notifies at `due_at`. Use the numeric ID
shown as `#7` with `show`, `done`, and `delete`.

Datetime values accept ISO-like local times such as:

```text
2026-06-20 18:00
2026-06-20T18:00
10m
2h
3d
```

Absolute times are interpreted with `TIMEZONE`, which defaults to `Asia/Tokyo`.
Relative values mean minutes, hours, or days from the current time.

## Development

Run tests that do not require Discord:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

## Operational notes

- Never commit `.env` or a real Discord bot token.
- Reminder times are stored as UTC in SQLite and displayed in `TIMEZONE`.
- If a notification fails because of channel permissions or a deleted channel, the bot records the error and retries after a short delay.
- Notification messages only allow the configured assignee mention; arbitrary mentions in titles or descriptions are not expanded.
- Completing a reminder is limited to the creator, assignee, or members with Manage Messages permission.
- Back up the SQLite database file under `data/` if reminders matter operationally.
- Keep the host machine clock accurate; reminder delivery depends on system time.

## Troubleshooting

- Slash commands do not appear: set `DISCORD_GUILD_ID` for local development and restart the bot.
- Slash commands still do not appear: confirm the bot was invited with the `applications.commands` scope.
- Bot cannot post reminders: check the bot has Send Messages permission in the target channel.
- `ModuleNotFoundError: reminder_bot`: install with `pip install -e .` or set `$env:PYTHONPATH='src'`.
- `Asia/Tokyo` timezone is missing on Windows: install dependencies from `pyproject.toml`; the `tzdata` package is included.
- `DISCORD_TOKEN is required`: copy `.env.example` to `.env` and set `DISCORD_TOKEN`.
- Login fails: regenerate the Bot Token in the Developer Portal and update `.env`.
