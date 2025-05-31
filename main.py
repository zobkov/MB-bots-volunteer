import asyncio
import logging
import logging.config

from aiogram import Bot, Dispatcher

from handlers import admin, other, user, task_creation, task_edit
from keyboards.set_menu import set_main_menu
from config_data.config import Config, load_config
from utils.logger.logging_settings import logging_config
from database.pg_model import create_pool
from middleware.registration import RoleAssigmmentMiddleware

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
    
    # Create PostgreSQL connection pool
    dp["pool"] = await create_pool(
        user=config.db.user,
        password=config.db.password,
        database=config.db.database,
        host=config.db.host,
        port=config.db.port
    )

    logger.info("Initialized bot and dispatcher")

    # Register middleware for all update types
    dp.update.outer_middleware(RoleAssigmmentMiddleware(dp["pool"]))  

    await set_main_menu(bot)
    logger.debug("Set main menu")

    dp.include_router(task_edit.router)
    dp.include_router(task_creation.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)
    dp.include_router(other.router)

    logger.info("Registered routers")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())