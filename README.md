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

## Notes
- Doma client is stubbed; replace endpoints in `doma/client.py` when available.
- CTA link is placeholder; update to proper Doma testnet route.
- DB file: `./bot.db` in working directory.
