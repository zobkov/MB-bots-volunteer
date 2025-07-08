from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from lexicon.lexicon_ru import LEXICON_RU
from keyboards.admin import get_menu_markup

router = Router()

@router.message(CommandStart())
async def proccess_start_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=LEXICON_RU["main"],
        reply_markup=get_menu_markup("main")
    )