import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from cachetools import TTLCache
from datetime import timedelta
from database.pg_model import User

logger = logging.getLogger(__name__)

class RoleAssigmmentMiddleware(BaseMiddleware):
    def __init__(self, pool) -> None:
        self.pool = pool
        self.role_cache = TTLCache(maxsize=1000, ttl=timedelta(hours=1).total_seconds())

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Always add pool and middleware to data
        data["pool"] = self.pool
        data["middleware"] = self
        
        logger.debug(f"Middleware called with event type: {type(event)}")
        
        # Handle different event types
        user = None
        if hasattr(event, "message") and event.message:
            user = event.message.from_user
        elif hasattr(event, "callback_query") and event.callback_query:
            user = event.callback_query.from_user
        elif hasattr(event, "from_user"):
            user = event.from_user
            
        if not user:
            logger.warning(f"Could not extract user from event type: {type(event)}")
            return await handler(event, data)
            
        user_id = user.id
        logger.debug(f"Processing user {user_id}")

        # Check if role is in cache first
        if user_id in self.role_cache:
            data["role"] = self.role_cache[user_id]
            logger.debug(f"Role retrieved from cache for user {user_id}: {data['role']}")
            return await handler(event, data)
        
        # If not in cache, query database
        user_data = await User.get_by_tg_id(self.pool, user_id)
        if not user_data:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            return None
            
        # Store in cache and data
        self.role_cache[user_id] = user_data.role
        data["role"] = user_data.role
        logger.debug(f"Role assigned and cached for user {user_id}: {user_data.role}")
        
        return await handler(event, data)