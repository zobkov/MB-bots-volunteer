# filepath: /Users/artyomzobkov/MB-2025/MB-bots-volunteer/middleware/debug_auth.py
import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.pg_model import User

logger = logging.getLogger(__name__)

class DebugAuthMiddleware(BaseMiddleware):
    def __init__(self, pool, debug_auth_enabled: bool) -> None:
        self.pool = pool
        self.debug_auth_enabled = debug_auth_enabled
        logger.debug(f"DebugAuthMiddleware initialized with debug_auth_enabled={self.debug_auth_enabled}")

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if not self.debug_auth_enabled:
            logger.debug(f"Debug_auth middleware is not called")
            return await handler(event, data)

        logger.debug(f"Debug_auth middleware IS called")
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user:
            tg_id = user.id
            username = user.username or "unknown"
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

            async with self.pool.acquire() as conn:
                existing_user = await conn.fetchrow(
                    "SELECT * FROM users WHERE tg_id = $1", tg_id
                )
                if not existing_user:
                    await conn.execute(
                        """
                        INSERT INTO users (tg_id, tg_username, name, role)
                        VALUES ($1, $2, $3, 'volunteer')
                        """,
                        tg_id, username, full_name
                    )
                    logger.info(f"New user added: {tg_id}, @{username}, {full_name}")

        return await handler(event, data)