# Doma Domain Alert Bot (Track 3)

Minimal Telegram bot that delivers domain alerts from Doma testnet and provides CTA to on-chain actions. Built for a 5-day MVP.

## Stack
- Python 3.11, aiogram v3 (polling)
- httpx (async HTTP), SQLite + SQLAlchemy (async)
- dotenv config, backoff, pytest (optional)

## Setup
1) Create venv and install deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure env
```bash
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN and DOMA settings
```

3) Run
```bash
python main.py
```

## Commands
- /start, /help
- /sub_add <filter>
- /sub_list
- /sub_del <id>
- /alert_test <domain>

## D2: Background Poller (Simulation mode)
- A background poller fetches events (kind from `DOMA_EVENT_KIND`) every `POLL_INTERVAL_SECONDS`.
- Simulation can be toggled via `DOMA_SIMULATE=true|false`. When true, events are randomly generated.
- Delivered events are deduped using `delivered_alerts` table.

Env keys:
```
POLL_INTERVAL_SECONDS=15
DOMA_EVENT_KIND=expiring
DOMA_SIMULATE=true
```

## Notes
- Doma client is stubbed; replace endpoints in `doma/client.py` when available.
- CTA link is placeholder; update to proper Doma testnet route.
- DB file: `./bot.db` in working directory.
- Security: never commit real tokens/keys; keep them in `.env`.
