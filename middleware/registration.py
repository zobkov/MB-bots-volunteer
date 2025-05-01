import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiogram.exceptions import TelegramBadRequest

from cachetools import TTLCache
from datetime import timedelta

from database.sqlite_model import User

logger = logging.getLogger(__name__)

class RoleAssigmmentMiddleware(BaseMiddleware):
    def __init__(self, conn) -> None:
        self.conn = conn
        self.role_cache = TTLCache(maxsize=1000, ttl=timedelta(hours=1).total_seconds())

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        logger.debug(f"Middleware called with event type: {type(event)}")
        
        # Handle different event types
        if hasattr(event, "message"):
            user = event.message.from_user
        elif hasattr(event, "callback_query"):
            user = event.callback_query.from_user
        elif hasattr(event, "from_user"):
            user = event.from_user
        else:
            logger.debug(f"Unhandled event type: {type(event)}")
            return await handler(event, data)
            
        user_id = user.id
        logger.debug(f"Processing user {user_id}")

        # Check if role is in cache first
        if user_id in self.role_cache:
            data["role"] = self.role_cache[user_id]
            data["middleware"] = self
            logger.debug(f"Role retrieved from cache for user {user_id}: {data['role']}")
            return await handler(event, data)
        
        # If not in cache, query database
        role = await User.exists(self.conn, user_id)
        if role is None:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            return None
            
        # Store in cache and data
        self.role_cache[user_id] = role
        data["role"] = role
        data["middleware"] = self
        logger.debug(f"Role assigned and cached for user {user_id}: {role}")
        data["main_outer_middleware"] = self
        
        return await handler(event, data)