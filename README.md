# Discord リマインダー Bot

Discordサーバー上の共同作業で、工程ごとのリマインダーを指定チャンネルへ投稿するBotです。

## MVPの範囲

- `/reminder add` でリマインダーを登録する
- `/reminder list` で未完了リマインダーを一覧表示する
- `/reminder show` でリマインダー詳細を確認する
- `/reminder done` でリマインダーを完了にする
- `/reminder delete` でリマインダーを削除する
- 通知日時になったら指定チャンネルへ投稿する
- Botを再起動してもSQLiteに保存した予定を維持する

## セットアップ

1. Discord Developer PortalでApplicationを作成します。
2. ApplicationのBotページを開き、Botを作成してTokenをコピーします。
3. このMVPではPrivileged Gateway Intentsは不要です。Message Content、Server Members、Presence intentsはOFFのままで構いません。
4. 開発中にスラッシュコマンドを早く反映したい場合は、Discordの開発者モードをONにして、テストサーバーIDをコピーします。
5. OAuth2 URL Generatorを開き、Scopesで以下を選択します。
   - `bot`
   - `applications.commands`
6. Bot Permissionsで以下を選択します。
   - View Channels
   - Send Messages
   - Embed Links
7. 生成されたURLを開き、Botをテストサーバーへ招待します。
8. `.env.example` を `.env` にコピーします。
9. `.env` の `DISCORD_TOKEN` にBot Tokenを設定します。
10. 開発中は `.env` の `DISCORD_GUILD_ID` にテストサーバーIDを設定します。
11. 依存関係をインストールします。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

12. Botを起動します。

```powershell
python -m reminder_bot.bot
```

`DISCORD_GUILD_ID` を設定すると、スラッシュコマンドが指定サーバーへ同期されやすくなります。未設定の場合はグローバル同期になり、Discord側で反映に時間がかかることがあります。

`pip install -e .` ではなく `pip install -r requirements.txt` でインストールする場合は、起動前に `PYTHONPATH` を設定してください。

```powershell
$env:PYTHONPATH='src'
python -m reminder_bot.bot
```

## Bot権限

Bot招待時に必要な主な権限は以下です。

- `bot`
- `applications.commands`
- Send Messages
- View Channels

View ChannelsとSend Messagesのみを権限値で指定する場合は `3072` です。通知先にする各チャンネルで、Botが閲覧と送信をできる必要があります。

## コマンド

```text
/reminder add title due_at description assignee remind_at channel
/reminder list include_done
/reminder show reminder_id
/reminder done reminder_id
/reminder delete reminder_id
```

使用例:

```text
/reminder add title:"資料レビュー" due_at:"2h" assignee:@tanaka
/reminder add title:"公開前チェック" due_at:"2026-06-20 18:00" remind_at:"2026-06-20 17:30" channel:#作業通知
/reminder list
/reminder show reminder_id:7
/reminder done reminder_id:7
/reminder delete reminder_id:7
```

`remind_at` を省略すると、Botは `due_at` の時刻に通知します。`show`、`done`、`delete` では、一覧に表示される `#7` のようなIDの数字部分を使います。

日時入力は以下の形式に対応しています。

```text
2026-06-20 18:00
2026-06-20T18:00
10m
2h
3d
```

絶対時刻は `TIMEZONE` のタイムゾーンで解釈されます。デフォルトは `Asia/Tokyo` です。相対指定は、現在時刻からの分・時間・日数として扱われます。

## 開発

Discord接続なしで実行できるテスト:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

構文チェック:

```powershell
python -m compileall src tests
```

## 運用上の注意

- `.env` や実際のDiscord Bot Tokenは絶対にコミットしないでください。
- リマインダー時刻はSQLite内ではUTCで保存し、表示時に `TIMEZONE` へ変換します。
- チャンネル権限不足やチャンネル削除などで通知に失敗した場合、Botはエラーを記録し、短い間隔を空けて再試行します。
- 通知メッセージでは、設定された担当者メンションのみを許可します。タイトルや説明文に含まれる任意のメンションは展開されません。
- リマインダーを完了にできるのは、作成者、担当者、またはManage Messages権限を持つメンバーです。
- リマインダーが業務上重要な場合は、`data/` 配下のSQLiteデータベースを定期的にバックアップしてください。
- 通知時刻は実行環境のシステム時刻に依存するため、ホストマシンの時刻を正確に保ってください。

## トラブルシュート

- `/reminder` が表示されない: 開発中は `DISCORD_GUILD_ID` を設定してBotを再起動してください。
- それでもスラッシュコマンドが表示されない: Bot招待時に `applications.commands` scopeを含めたか確認してください。
- Botが通知を投稿しない: 通知先チャンネルでBotにView ChannelsとSend Messages権限があるか確認してください。
- `ModuleNotFoundError: reminder_bot` が出る: `pip install -e .` でインストールするか、`$env:PYTHONPATH='src'` を設定してください。
- Windowsで `Asia/Tokyo` が見つからない: 依存関係をインストールしてください。`tzdata` パッケージを含めています。
- `DISCORD_TOKEN is required` が出る: `.env.example` を `.env` にコピーし、`DISCORD_TOKEN` を設定してください。
- Discordログインに失敗する: Developer PortalでBot Tokenを再発行し、`.env` を更新してください。

## 現在の開発状況

MVPのコード実装と単体テストは完了しています。次に必要なのは、実際のDiscordテストサーバーでBotを起動し、スラッシュコマンド登録・リマインダー作成・チャンネル通知を確認することです。
