import asyncio
import logging
import logging.config
from environs import Env
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor  # Add this import

from aiogram import Bot, Dispatcher, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers import admin, other, user, task_creation, task_edit, assignment, volunteer_management, admin_start, vol_start
from filters.roles import IsAdmin, IsVolunteer
from keyboards.set_menu import set_main_menu
from config_data.config import Config, load_config
from utils.logger.logging_settings import logging_config
from database.pg_model import create_pool  
from middleware.registration import RoleAssigmmentMiddleware
from utils.event_time import EventTimeManager

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

"""
git pull
sudo systemctl restart volunteer_bot
sudo systemctl status volunteer_bot

"""



async def main() -> None:
    config: Config = load_config()
    if config == -1:
        logger.critical("Error reading configuration")
        exit(-1)

    logger.info(f"Loaded EVENT_START_DATE: {config.event.start_date}")
    logger.info("Loaded bot configuration")



    start_date=config.event.start_date
    days_count=config.event.days_count
    debug_mode=config.event.debug_mode

    if debug_mode:
        logger.warning("DEBUG MODE IS ON")
        logger.warning("DEBUG "*100)
        logger.warning("DEBUG MODE IS ON")

    logger.info(f"Current start date: {start_date.isoformat(" ")} with {days_count} days")

    # Create event time manager
    event_manager = EventTimeManager(
        start_date,
        days_count,
        debug_mode
    )
    bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    logger.info("Initialized bot and dispatcher")

    # Add event manager to dispatcher data
    dp["event_manager"] = event_manager

    dp["spot_duration"] = config.spot_duration
    
    # Create PostgreSQL connection pool
    try:
        dp["pool"] = await create_pool(
            user=config.db.user,
            password=config.db.password,
            database=config.db.database,
            host=config.db.host,
            port=config.db.port
        )
    except Exception as e:
        logger.critical(f"ERROR CONNECTING TO THE DATABASE: {e}")
        exit(-1)

    logger.info("Successfully created DB connection")

    # Register middleware based on debug_auth mode

    dp.update.outer_middleware(RoleAssigmmentMiddleware(dp["pool"], config.debug_auth))



    await set_main_menu(bot)
    logger.debug("Set main menu")

    admin_router = Router(name="admin_router")
    admin_router.message.filter(IsAdmin())
    admin_router.callback_query.filter(IsAdmin())

    admin_router.include_router(admin_start.router)
    
    admin_router.include_routers(task_edit.router, task_creation.router, volunteer_management.router, assignment.router, admin.router)


    vol_router = Router(name="vol_router")
    vol_router.message.filter(IsVolunteer())
    vol_router.callback_query.filter(IsVolunteer())

    vol_router.include_router(vol_start.router)

    vol_router.include_routers(user.router)

    dp.include_router(admin_router)
    dp.include_router(vol_router)

    if config.event.debug_mode:
        dp["debug"]=True
        from handlers import debug
        dp.include_router(debug.router)

    dp.include_router(other.router)

    logger.info("Registered routers")

    # Configure scheduler with SQLAlchemy jobstore
    jobstores = {
        'default': SQLAlchemyJobStore(
            url=f'postgresql://{config.db.user}:{config.db.password}@{config.db.host}:{config.db.port}/{config.db.database}'
        )
    }
    executors = {
        'default': AsyncIOExecutor()  # Use AsyncIOExecutor instead of ThreadPoolExecutor
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3,
        'misfire_grace_time': None  # Add this to prevent misfires
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults
    )
    scheduler.start()
    dp["scheduler"] = scheduler

    await bot.delete_webhook(drop_pending_updates=True)
    logger.debug("Deleted webhook. All prior updates are dropped")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())