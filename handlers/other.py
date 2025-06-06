import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from lexicon.lexicon_ru import LEXICON_RU
from database.pg_model import User, PendingUser

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("add_user"))
async def add_user_handler(message: Message, command: Command, pool=None):
    if not command.args:
        logger.warning(f"User {message.from_user.username} has used /add_user incorrectly")
        return await message.reply("Использование: /add_user username role Полное Имя")
        
    parts = command.args.split(maxsplit=2)
    if len(parts) < 3:
        logger.warning(f"User {message.from_user.username} has used /add_user incorrectly")
        return await message.reply("Нужно указать три параметра: /add_user username role Полное Имя")

    username, role, name = parts

    if role not in ('volunteer', 'admin'):
        logger.warning(f"User {message.from_user.username} has used /add_user incorrectly. Incorrect role: {role}")
        return await message.reply("Роль должна быть volunteer или admin")
    
    if pool is None:
        logger.error("No connection to the database")
        return await message.reply("Lost connection to the database")

    # Remove @ from username if present
    username = username.lstrip('@')

    # Create pending user
    await PendingUser.create(pool, username, name, role)
    await message.reply(f"Пользователь {name} @{username} добавлен в список ожидающих с ролью '{role}'")
    logger.info(f"Pending user @{username} ({name}, {role}) has been added by {message.from_user.username}")

@router.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext):
    logger.debug(f"User {message.from_user.username} (id:{message.from_user.id}) issued /start")

@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    logger.debug(f"User {message.from_user.username} (id:{message.from_user.id}) issued /help")
    await message.answer(text=LEXICON_RU['/help'])

@router.message()
async def proccess_unexpected_message(message: Message):
    await message.answer("Произошла ошибка или бот ожидал другое сообщение/действие")
    logger.info(f"User {message.from_user.username} (id={message.from_user.id}) has made an unexpected action. Effectively -> event is unhandled")