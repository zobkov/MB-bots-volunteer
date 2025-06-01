import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from lexicon.lexicon_ru import LEXICON_RU
from database.pg_model import User

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("add_user"))
async def add_user_handler(message: Message, command: Command, pool=None):
    if not command.args:
        logger.warning(f"User {message.from_user.username} has used /add_user incorrectly. Needed 4 arguments")
        return await message.reply("Использование: /add_user <id> <username> <name> <role>")
        
    parts = command.args.split()
    if len(parts) != 4:
        logger.warning(f"User {message.from_user.username} has used /add_user incorrectly. Needed 4 arguments")
        return await message.reply("Нужно указать именно два аргумента: /add_user <id> <username> <name> <role>")

    id, username, name, role = parts  

    if role not in ('volunteer', 'admin'):
        logger.warning(f"User {message.from_user.username} has used /add_user incorrectly. Incorrect role: {role}")
        return await message.reply("Invalid role. should be volunteer or admin")
    
    if pool is None:
        logger.error("No connection to the database")
        return await message.reply("Lost connection to the database")

    await message.reply(f"Пользователь {name} @{username} (id={id}) будет добавлен с ролью '{role}'")
    created_user = await User.create(pool, id, username, name, role)
    logger.info(f"User (f{created_user.name} {created_user.tg_username} {created_user.role}) has been added to the database by {message.from_user.username} (id={message.from_user.id})")

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