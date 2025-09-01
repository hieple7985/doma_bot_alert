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

settings = Settings()
