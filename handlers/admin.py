import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from lexicon.lexicon_ru import LEXICON_RU

from database.sqlite_model import User

from filters.roles import IsAdmin

logger = logging.getLogger(__name__)

# Use this:
router = Router()
router.message.filter(IsAdmin())

# Then define your handlers
@router.message(CommandStart())
async def admin_handler(message: Message):
    await message.reply("Hello, fellow admin! Welcome to this bot")

@router.message(Command(commands=['change_roles']))
async def admin_handler(message: Message, conn=None, middleware=None, **data):  # Changed from main_outer_middleware to middleware
    if conn and middleware:
        # Update role in database
        await User.update_role(conn, message.from_user.id, "volunteer")
        
        # Update cache in middleware
        middleware.role_cache[message.from_user.id] = "volunteer"
        
        # Update workflow data
        data["role"] = "volunteer"
        
        logger.info(f"User {message.from_user.username} (id={message.from_user.id}) has switched role to 'volunteer'")
        await message.answer("Role changed to volunteer")
    else:
        logger.error(f"User {message.from_user.username} (id={message.from_user.id}) tried to switch roles but missing connection or middleware")
        await message.answer("Configuration error")
