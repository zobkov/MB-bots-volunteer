# filepath: /Users/artyomzobkov/MB-2025/MB-bots-volunteer/middleware/debug_auth.py
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update
from cachetools import TTLCache
from datetime import timedelta
from database.pg_model import User

logger = logging.getLogger(__name__)

class DebugAuthMiddleware(BaseMiddleware):
    def __init__(self, pool, debug_auth_enabled: bool) -> None:
        self.pool = pool
        self.debug_auth_enabled = debug_auth_enabled
        self.role_cache = TTLCache(maxsize=1000, ttl=timedelta(hours=1).total_seconds())
        logger.debug(f"DebugAuthMiddleware initialized with debug_auth_enabled={self.debug_auth_enabled}")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not self.debug_auth_enabled:
            logger.debug("DebugAuthMiddleware is not active")
            return await handler(event, data)

        logger.debug("DebugAuthMiddleware is active")
        user = None

        # Handle different event types
        if isinstance(event, Update):
            if event.message:
                user = event.message.from_user
            elif event.callback_query:
                user = event.callback_query.from_user
        elif isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if not user:
            logger.warning(f"Could not extract user from event type: {type(event)}")
            return await handler(event, data)

        user_id = user.id
        username = user.username or "unknown"
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

        # Check cache first
        if user_id in self.role_cache:
            data["role"] = self.role_cache[user_id]
            logger.debug(f"Role retrieved from cache for user {user_id}: {data['role']}")
            return await handler(event, data)

        # Check database
        async with self.pool.acquire() as conn:
            existing_user = await conn.fetchrow(
                "SELECT * FROM users WHERE tg_id = $1", user_id
            )
            if not existing_user:
                # Add user to the database with default role 'volunteer'
                await conn.execute(
                    """
                    INSERT INTO users (tg_id, tg_username, name, role)
                    VALUES ($1, $2, $3, 'volunteer')
                    """,
                    user_id, username, full_name
                )
                logger.info(f"New user added: {user_id}, @{username}, {full_name}")
                role = "volunteer"
            else:
                role = existing_user["role"]
                logger.debug(f"User already exists in the database: {user_id}, @{username}, {full_name}")

        # Update cache and data
        self.role_cache[user_id] = role
        data["role"] = role
        logger.debug(f"Role assigned and cached for user {user_id}: {role}")

        return await handler(event, data)