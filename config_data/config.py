import logging
from datetime import datetime
from typing import Optional
import os
from environs import Env

logger = logging.getLogger(__name__)

from dataclasses import dataclass


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
    env = Env()
    env.read_env()  # Read environment variables from .env file

    return Config(
        tg_bot=TgBot(token=env.str("BOT_TOKEN")),
        db=DatabaseConfig(
            user=env.str("DB_USER"),
            password=env.str("DB_PASS"),
            database=env.str("DB_NAME"),
            host=env.str("DB_HOST"),
            port=env.int("DB_PORT", 5432)
        ),
        event=EventConfig(
            start_date=env.datetime("EVENT_START_DATE"),
            days_count=env.int("EVENT_DAYS_COUNT"),
            debug_mode=env.bool("DEBUG_MODE", False)
        ),
        debug_auth=env.bool("DEBUG_AUTH", False)
    )