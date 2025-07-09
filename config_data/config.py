import logging
from datetime import datetime
from typing import Optional
import os
import json
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
    spot_duration: int
    api_cred: str
    debug_auth: bool = False 

def load_config() -> Config:
    # Загружаем JSON конфигурацию
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        json_config = json.load(f)
    
    # Загружаем переменные окружения для секретных данных
    env = Env()
    env.read_env()
    
    logger.debug("Loading configuration from JSON and environment variables")
    logger.debug(f"JSON config: {json_config}")

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
            start_date=datetime.strptime(json_config["event_config"]["start_date"], "%Y-%m-%d"),
            days_count=json_config["event_config"]["days_count"],
            debug_mode=json_config.get("debug", False)
        ),
        debug_auth=json_config.get("debug_config", {}).get("debug_auth", False),
        spot_duration=json_config["event_config"]["spot_duration"],
        api_cred=env.str("API_CRED")
    )