import logging

from typing import Union, Dict, Any
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


class IsAdmin(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], **data) -> bool:
        role = data.get("role")
        logger.debug(f"IsAdmin filter called with role: {role}")
        return role == "admin"

class IsVolunteer(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], **data) -> bool:
        role = data.get("role")
        logger.debug(f"IsVolunteer filter called with role: {role}")
        return role == "volunteer"