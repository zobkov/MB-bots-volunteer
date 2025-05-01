import logging


from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from states.states import FSMRole

from lexicon.lexicon_ru import LEXICON_RU

from database.sqlite_model import User

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext, conn):
    logger.debug(f"User {message.from_user.username} (id:{message.from_user.id}) issued /start")

        



@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    logger.debug(f"User {message.from_user.username} (id:{message.from_user.id}) issued /help")

    await message.answer(text=LEXICON_RU['/help'])