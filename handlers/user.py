import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from lexicon.lexicon_ru import LEXICON_RU

from filters.roles import IsVolunteer

from database.sqlite_model import User

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsVolunteer())

@router.message(CommandStart())
async def proccess_start(message: Message):
    await message.reply("Hi :/")

@router.message(Command(commands=['change_roles']))
async def admin_handler(message: Message, conn=None, middleware=None, **data):
    if conn and middleware:
        # Update role in database
        await User.update_role(conn, message.from_user.id, "admin")
        
        # Update cache in middleware
        middleware.role_cache[message.from_user.id] = "admin"
        
        # Update workflow data
        data["role"] = "admin"
        
        logger.info(f"User {message.from_user.username} (id={message.from_user.id}) has switched role to 'admin'")
        await message.answer("Role changed to admin")
    else:
        logger.error(f"User {message.from_user.username} (id={message.from_user.id}) tried to switch roles but missing connection or middleware")
        await message.answer("Configuration error")
