# Discord用リマインダーbot 開発コンテキスト

最終更新: 2026-06-19

## プロジェクト停止理由

このプロジェクトは一旦ここで開発停止とする。

理由は、Renderでの常時稼働に想定よりもコストがかかるため。Discord botは常時オンラインでDiscord Gatewayへ接続し続ける必要があり、Renderの無料Web Serviceではスリープや永続データ消失の懸念がある。安定運用にはBackground Workerと永続ディスクが必要だが、この構成は有料利用が前提になる。

将来、本格的に使いたくなった時に再開できるよう、ここまでの実装状況と再開時の注意点をこのファイルに残す。

## 現在の実装状況

Python製のDiscordリマインダーbotとして、基本機能は実装済み。

- Discord slash commandでリマインダーを登録できる
- 指定時刻になるとDiscordチャンネルへ通知する
- SQLiteでリマインダーを永続化する
- `/reminder add` と `/reminder delete` を実装済み
- 時刻入力は `2m` のような相対指定や、引用符付きの `"2m"` に対応済み
- 通知重複対策を実装済み
- 古い重複pendingリマインダーの通知時整理を実装済み
- Discordコマンドの重複登録対策を実装済み
- Windows環境での証明書問題対策として `truststore` を導入済み
- README、利用規約、プライバシーポリシーを日本語で作成済み
- Render向けのデプロイ設定を追加済み

## リポジトリ

- GitHub: `https://github.com/AdvanceHacker9361/discord-reminder-bot`
- 公開設定: public
- 現在ブランチ: `master`
- 最新確認済みコミット: `9b2a740 Add Render deployment configuration`

## 主要ファイル

- `src/reminder_bot/bot.py`
  - Discord bot本体
  - `truststore.inject_into_ssl()` をDiscord import前に実行
  - slash command同期処理
  - `DISCORD_GUILD_ID` がある場合はguild command優先

- `src/reminder_bot/commands/reminder.py`
  - `/reminder add`
  - `/reminder delete`
  - Discord slash commandの入力処理

- `src/reminder_bot/reminder_service.py`
  - SQLiteを使ったリマインダー登録、取得、削除、通知claim処理
  - 重複登録防止
  - 通知時の重複pending整理

- `src/reminder_bot/scheduler.py`
  - 一定間隔で期限切れリマインダーを確認
  - Discordチャンネルへ通知
  - 通知失敗時の記録

- `src/reminder_bot/time_parser.py`
  - 相対時刻、絶対時刻、引用符付き入力の解析

- `src/reminder_bot/formatting.py`
  - 登録結果や通知メッセージの整形

- `src/reminder_bot/database.py`
  - SQLite接続と初期化

- `render.yaml`
  - Render Background Worker向け設定
  - `DATABASE_PATH=/var/data/reminders.sqlite3`
  - 永続ディスク `/var/data`
  - `numInstances: 1`

- `.python-version`
  - Python `3.13.5`

- `.env.example`
  - 必要な環境変数のサンプル
  - 実トークンは含めない

- `TERMS_OF_SERVICE.md`
  - サービス利用規約

- `PRIVACY_POLICY.md`
  - プライバシーポリシー

## 必要な環境変数

`.env` はローカル専用で、Gitには含めない。

```env
DISCORD_TOKEN=replace-with-your-bot-token
DISCORD_GUILD_ID=replace-with-your-discord-server-id
DATABASE_PATH=data/reminders.sqlite3
TIMEZONE=Asia/Tokyo
REMINDER_POLL_INTERVAL_SECONDS=30
```

注意:

- `DISCORD_TOKEN` は絶対にGitHubへpushしない
- `DISCORD_GUILD_ID` は単一サーバーで早くコマンド同期したい場合に使う
- 複数サーバー対応にする場合は `DISCORD_GUILD_ID` を未設定にし、グローバルコマンド同期にする
- ローカル起動とクラウド起動を同時に行うと、通知や登録処理が重複する可能性がある

## ローカル起動方法

```powershell
cd C:\Users\addvl\OneDrive\ドキュメント\Discord用リマインダーbot
.\.venv\Scripts\Activate.ps1
python -m reminder_bot.bot
```

起動ログに次のような表示が出ればDiscord Gateway接続は成功。

```text
Shard ID None has connected to Gateway
```

## テスト

最後に確認したテスト:

```powershell
python -m unittest discover -s tests
python -m compileall src tests
```

確認済み結果:

- unit test: 26件 OK
- compileall: OK
- 秘密情報スキャン: 実トークン混入なし

## Render運用メモ

Renderで安定運用する場合の想定構成:

- Service type: Background Worker
- Plan: Starter以上
- Persistent Disk: `/var/data`
- Database path: `/var/data/reminders.sqlite3`
- Instance count: 1

Render無料枠だけでの本番運用は推奨しない。

理由:

- Background Workerは無料枠対象外
- 無料Web Serviceは15分程度の無通信でスリープする
- 無料Web Serviceは永続ディスクを使えない
- SQLite保存データが再起動や再デプロイで失われる可能性がある

Renderで本番稼働させる場合は、ローカルPC上のbotを停止すること。同じBot Tokenで複数プロセスを動かすと、重複処理の原因になる。

## 将来再開する場合の選択肢

### 1. Render有料で再開

最も簡単。すでに `render.yaml` があるため、GitHub連携後に環境変数を入れれば開始しやすい。

再開時にやること:

1. RenderでBlueprintまたはBackground Workerを作成
2. `DISCORD_TOKEN` を設定
3. 必要なら `DISCORD_GUILD_ID` を設定
4. Persistent Diskが `/var/data` にマウントされていることを確認
5. LogsでDiscord Gateway接続を確認
6. Discord上で `/reminder` が表示されることを確認

### 2. 無料VPS系へ移行

月額コストを抑えるなら、Oracle Cloud Always Freeなどの無料VPSに移す方法がある。

メリット:

- 常時稼働しやすい
- SQLiteをそのまま使いやすい
- Renderより月額費用を抑えられる可能性がある

デメリット:

- サーバー初期設定が必要
- `systemd` などで常駐化する必要がある
- OS更新、ログ管理、バックアップなどの運用が必要

### 3. データ保存先をクラウドDBへ変更

Render無料Web Serviceを使う場合でも、SQLiteではなく外部DBを使えばデータ消失リスクは下げられる。ただし無料DBには期限や制限があるため、リマインダーbotの本番利用には注意が必要。

候補:

- PostgreSQL
- Supabase
- Neon
- SQLite互換の外部サービス

この場合、`reminder_service.py` と `database.py` の設計変更が必要。

## 既知の注意点

- Discordのslash commandは反映まで時間がかかる場合がある
- `DISCORD_GUILD_ID` を設定すると、そのサーバーに限定してコマンド同期される
- `DISCORD_GUILD_ID` 未設定の場合はグローバルコマンドになり、反映に時間がかかる
- 過去にコマンドが重複表示されたため、現在はguild command同期とglobal command整理の処理を入れている
- 通知重複は、同一Bot Tokenで複数プロセスを起動した場合にも起きうる
- SQLite運用では複数インスタンスに増やさない

## 再開時に最初に確認すること

1. `git status --short --branch`
2. `.env` に `DISCORD_TOKEN` と必要な環境変数があるか
3. `python -m unittest discover -s tests`
4. `python -m compileall src tests`
5. ローカル起動でDiscord Gatewayに接続できるか
6. テスト用サーバーで `/reminder add` と通知を確認

## 最後の状態

この時点では、ローカル開発とテスト用サーバーでの動作確認は完了している。常時稼働の本番運用だけが、コスト面の理由で保留。

