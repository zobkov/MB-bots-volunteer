import logging
from datetime import datetime
from typing import Optional
import os

logger = logging.getLogger(__name__)

from dataclasses import dataclass
from environs import Env


@dataclass
class EventConfig:
    start_date: datetime  # Дата начала мероприятия
    days_count: int       # Количество дней мероприятия
    debug_mode: bool = False
    debug_current_time: datetime | None = None

@dataclass
class DatabaseConfig:
    user: str
    password: str
    database: str
    host: str
    port: int = 5432

@dataclass
class TgBot:
    token: str

@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig
    event: EventConfig
    debug_auth: bool = False  # Add this parameter

def load_config() -> Config:
    return Config(
        tg_bot=TgBot(token=os.getenv("BOT_TOKEN")),
        db=DatabaseConfig(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 5432))
        ),
        event=EventConfig(
            start_date=datetime.fromisoformat(os.getenv("EVENT_START_DATE")),
            days_count=int(os.getenv("EVENT_DAYS_COUNT")),
            debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true"
        ),
        debug_auth=os.getenv("DEBUG_AUTH", "true").lower() == "true"  # Load debug_auth
    )