#!/usr/bin/env python3
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
    doma_base_url: str = os.getenv("DOMA_BASE_URL", "https://start.doma.xyz/api")
    doma_private_key_test: str = os.getenv("DOMA_PRIVATE_KEY_TEST", "")
    debug: bool = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    # D2 knobs
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "15"))
    doma_event_kind: str = os.getenv("DOMA_EVENT_KIND", "expiring")
    doma_simulate: bool = os.getenv("DOMA_SIMULATE", "true").lower() in {"1", "true", "yes"}
    alerts_dry_run: bool = os.getenv("ALERTS_DRY_RUN", "true").lower() in {"1", "true", "yes"}

settings = Settings()
