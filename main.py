import asyncio
import logging
import logging.config

# aiogram imports
from aiogram import Bot, Dispatcher, F

# handlers
from handlers import user_handlers, admin_handlers, other_handlers

# main menu
from keyboards.set_menu import set_main_menu

# config module
from config_data.config import Config, load_config

# logger settings
from utils.logger.logging_settings import logging_config


logging.config.dictConfig(logging_config)

logger = logging.getLogger(__name__)


async def main() -> None:
    
    config: Config = load_config()
    if config == -1:
        logger.critical("Error reading configuration")
        exit(-1)
    
    logger.info("Loaded bot configuration")

    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher()

    logger.info("Initialized bot and dispatcher")

    await set_main_menu(bot)
    logger.debug("Set main menu")

    dp.include_router(other_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    
    logger.info("Registered routers")
    
    await dp.start_polling(bot)



asyncio.run(main())