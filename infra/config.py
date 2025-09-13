#!/usr/bin/env python3
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
    # Default to testnet API per docs
    doma_base_url: str = os.getenv("DOMA_BASE_URL", "https://api-testnet.doma.xyz")
    doma_private_key_test: str = os.getenv("DOMA_PRIVATE_KEY_TEST", "")
    # API key/header for Doma HTTP calls (if required)
    doma_api_key: str = os.getenv("DOMA_API_KEY", "")
    doma_api_header: str = os.getenv("DOMA_API_HEADER", "Api-Key")
    debug: bool = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    # D2 knobs
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "15"))
    doma_event_kind: str = os.getenv("DOMA_EVENT_KIND", "expiring")
    doma_simulate: bool = os.getenv("DOMA_SIMULATE", "true").lower() in {"1", "true", "yes"}
    alerts_dry_run: bool = os.getenv("ALERTS_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    # Poll API filters
    doma_event_types: str = os.getenv("DOMA_EVENT_TYPES", "NAME_TOKEN_LISTED")
    doma_finalized_only: bool = os.getenv("DOMA_FINALIZED_ONLY", "true").lower() in {"1", "true", "yes"}

    # Webhook settings (optional)
    tg_webhook_base: str = os.getenv("TG_WEBHOOK_BASE", "")  # e.g., https://doma-bot-alert.onrender.com
    tg_webhook_path: str = os.getenv("TG_WEBHOOK_PATH", "tg-webhook")
    tg_webhook_secret: str = os.getenv("TG_WEBHOOK_SECRET", "")

settings = Settings()
