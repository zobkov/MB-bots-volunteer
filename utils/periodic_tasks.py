import logging
import asyncpg
from services.faq import FAQService

logger = logging.getLogger(__name__)

async def sync_faq_periodic(db_config: dict, cred_faq: dict):
    """Периодическая синхронизация FAQ"""
    try:
        if cred_faq:
            # Создаем пул соединений внутри задачи
            pool = await asyncpg.create_pool(**db_config)
            try:
                faq_service = FAQService(pool, cred_faq)
                result = await faq_service.sync_faq_from_google()
                logger.info(f"Periodic FAQ sync result: {result}")
            finally:
                await pool.close()
        else:
            logger.warning("FAQ credentials not configured, skipping sync")
    except Exception as e:
        logger.error(f"Error in periodic FAQ sync: {e}")