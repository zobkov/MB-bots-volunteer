import logging
from datetime import datetime
from typing import Optional
import os
import json
from environs import Env

logger = logging.getLogger(__name__)

from dataclasses import dataclass, field


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
class FAQConfig:
    auto_sync_enabled: bool = False
    sync_interval_minutes: int = 15

@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig
    event: EventConfig
    spot_duration: int
    api_cred_admin: str
    api_cred_faq: str
    debug_auth: bool = False
    faq: FAQConfig = field(default_factory=FAQConfig)  # Добавляем FAQ конфиг

def load_config(path: str = None) -> Config:
    # Загружаем JSON конфигурацию
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        json_config = json.load(f)
    
    # Загружаем переменные окружения для секретных данных
    env = Env()
    env.read_env()
    
    logger.debug("Loading configuration from JSON and environment variables")
    logger.debug(f"JSON config: {json_config}")

    tg_bot = TgBot(token=env.str("BOT_TOKEN"))
    db_config = DatabaseConfig(
        user=env.str("DB_USER"),
        password=env.str("DB_PASS"),
        database=env.str("DB_NAME"),
        host=env.str("DB_HOST"),
        port=env.int("DB_PORT", 5432)
    )
    event_config = EventConfig(
        start_date=datetime.strptime(json_config["event_config"]["start_date"], "%Y-%m-%d"),
        days_count=json_config["event_config"]["days_count"],
        debug_mode=json_config.get("debug", False)
    )
    
    # FAQ configuration
    faq_config_data = json_config.get('faq_config', {})
    faq_config = FAQConfig(
        auto_sync_enabled=faq_config_data.get('auto_sync_enabled', False),
        sync_interval_minutes=faq_config_data.get('sync_interval_minutes', 15)
    )
    
    return Config(
        tg_bot=tg_bot,
        db=db_config,
        event=event_config,
        spot_duration=json_config.get('event_config', {}).get('spot_duration', 30),
        api_cred_admin=env('API_CRED_ADMIN'),
        api_cred_faq=env('API_CRED_FAQ'),
        debug_auth=json_config.get('debug_config', {}).get('debug_auth', False),
        faq=faq_config  # Добавляем FAQ конфиг
    )