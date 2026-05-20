# r2-direct-download-alert-tgbot

Telegram Bot that sends alerts on Cloudflare R2 direct download

> platform: `macOS`

## Prerequisites

```yaml
node.js: 22.22.3
python: 3.10.20
```

```bash
brew install cloudflared
```

Telegram notifications for **all activity** across **all of your Cloudflare R2 buckets**:

| Event | How it is detected |
|-------|-------------------|
| **Download** (GET) | Cloudflare Worker proxy in front of each bucket |
| **Upload / overwrite** | R2 event notifications → Queue → Worker |
| **Delete** | R2 event notifications → Queue → Worker |

By default, **every file type** is included (`.mp4`, images, zips, etc.). R2 itself does not emit download events; uploads/deletes are native R2 notifications.

Designed to run on **macOS (Intel or Apple Silicon)**. Windows PowerShell scripts are still included.

## Architecture

```text
                    ┌─────────────────────────────────────┐
  Download (GET)    │  Cloudflare Worker                  │
  ───────────────►  │  /{bucket}/{object-key}  ──► R2    │──► webhook ──► Mac bot ──► Telegram
                    └─────────────────────────────────────┘

  Upload / delete   R2 bucket ──► Queue (r2-object-events) ──► Worker ──► webhook ──► Mac bot
```

Share download links as:

```text
https://YOUR-WORKER-DOMAIN/{bucket-name}/path/to/file.mp4
```

Direct `*.r2.dev` URLs bypass the Worker and will **not** trigger download alerts.

## macOS quick start (Intel MacBook)

### 1. Prerequisites

Install once:

- **Python 3.11+** — [python.org](https://www.python.org/downloads/macos/) or `brew install python@3.12`
- **Node.js LTS** — [nodejs.org](https://nodejs.org/) or `brew install node`
- **cloudflared** (optional tunnel) — `brew install cloudflared`

### 2. Clone / copy project to your Mac

```bash
cd ~/Projects/r2-download-alerts   # your path
cp .env.example .env
```

Edit `.env`:

- `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `TELEGRAM_CHAT_ID` — from [@userinfobot](https://t.me/userinfobot)
- `R2_BUCKETS` — **all** bucket names, comma-separated, e.g. `clips,archive,backups`
- `WEBHOOK_SECRET` — long random string
- Leave `ALERT_EXTENSIONS` **empty** to alert on all file types

### 3. One-time setup

```bash
chmod +x scripts/*.sh
./scripts/setup-mac.sh
make generate          # writes bucket bindings into worker/wrangler.toml
./scripts/setup-cloudflare.sh   # queue + upload/delete notifications per bucket
```

Log in to Cloudflare if prompted:

```bash
cd worker && npx wrangler login
```

### 4. Run the bot on your Mac

Terminal 1:

```bash
make run
# or: ./scripts/run-bot.sh
```

Terminal 2 — expose webhook (pick one):

```bash
make tunnel
# cloudflared prints https://xxxx.trycloudflare.com
```

Set in `worker/wrangler.toml` under `[vars]`:

```toml
WEBHOOK_URL = "https://xxxx.trycloudflare.com/webhook/event"
```

Set the Worker secret (same value as `WEBHOOK_SECRET` in `.env`):

```bash
cd worker
npx wrangler secret put WEBHOOK_SECRET
```

### 5. Test

```bash
make test
```

You should get a Telegram test message.

### 6. Deploy Worker

```bash
make deploy
```

Attach a route in Cloudflare dashboard (Workers → Domains & Routes), e.g. `media.example.com/*`.

### 7. (Optional) Run bot at login with launchd

```bash
mkdir -p logs
# Edit scripts/launchd/com.r2downloadalerts.bot.plist — replace /REPLACE/PROJECT/PATH
cp scripts/launchd/com.r2downloadalerts.bot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.r2downloadalerts.bot.plist
```

## What you get notified about

| Telegram title | When |
|----------------|------|
| R2 download | Someone GETs a file through the Worker URL |
| R2 upload / overwrite | PutObject, CopyObject, multipart complete (any bucket in `R2_BUCKETS`) |
| R2 delete | DeleteObject, lifecycle deletion |

Toggle types in `.env`:

```bash
NOTIFY_DOWNLOAD=true
NOTIFY_OBJECT_CREATE=true
NOTIFY_OBJECT_DELETE=true
```

## Multi-bucket download URLs

After `make generate`, each bucket is mounted under its **bucket name**:

```text
https://media.example.com/my-clips/videos/clip.mp4
https://media.example.com/my-archive/2024/backup.zip
```

## Configuration

| Variable | Purpose |
|----------|---------|
| `R2_BUCKETS` | All buckets to monitor (required) |
| `ALERT_EXTENSIONS` | Empty = **all files**; or `.mp4,.jpg` to filter |
| `IGNORE_IPS` | Skip download alerts from these IPs (your Mac/public IP) |
| `WEBHOOK_PATH` | Default `/webhook/event` |
| `DEDUPE_TTL_SECONDS` | Worker var — suppress repeat download alerts (default 600s) |

## Makefile commands

| Command | Action |
|---------|--------|
| `make install` | Python venv + dependencies |
| `make run` | Start webhook bot |
| `make test` | Send test event to local bot |
| `make generate` | Sync `wrangler.toml` buckets from `.env` |
| `make setup-cloudflare` | Create queue + R2 notifications |
| `make deploy` | Deploy Worker |
| `make tunnel` | Temporary public URL via cloudflared |

## Windows (optional)

```powershell
.\scripts\run-bot.ps1
.\scripts\test-webhook.ps1
```

Use Git Bash or WSL for `setup-cloudflare.sh` / `generate_worker_config.py`.

## Project layout

```text
r2-download-alerts/
  bot/                    # FastAPI + Telegram (runs on your Mac)
  worker/                 # Cloudflare Worker (proxy + queue consumer)
  scripts/
    setup-mac.sh          # macOS prerequisite check
    setup-cloudflare.sh   # Queue + per-bucket notifications
    generate_worker_config.py
    run-bot.sh
    test-webhook.sh
    launchd/              # Optional auto-start on macOS
  Makefile
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No Telegram messages | `make test`; verify token and chat ID |
| Upload/delete not alerting | Run `./scripts/setup-cloudflare.sh`; check queue `r2-object-events` in dashboard |
| Download not alerting | URL must be `/{bucket}/{key}` via Worker, not direct R2 URL |
| Unknown bucket (404) | Run `make generate` after changing `R2_BUCKETS`, then `make deploy` |
| Too many download alerts | Increase `DEDUPE_TTL_SECONDS` in `worker/wrangler.toml` |

## Security

- Use a strong `WEBHOOK_SECRET`
- Never commit `.env`
- Set `IGNORE_IPS` to your home IP when testing downloads

&copy; 2026 All rights reserved.
