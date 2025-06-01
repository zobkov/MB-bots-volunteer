import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from lexicon.lexicon_ru import LEXICON_RU, LEXICON_RU_BUTTONS
from filters.roles import IsVolunteer
from handlers.callbacks import NavigationCD
from keyboards.user import get_menu_markup
from keyboards.admin import get_menu_markup as get_admin_menu_markup
from database.pg_model import User

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
async def proccess_start(message: Message):
    await message.answer(
        text=LEXICON_RU["main"],
        reply_markup=get_menu_markup("main")
    )

@router.message(Command(commands=['change_roles']))
async def role_change_handler(message: Message, pool=None, middleware=None, **data):
    if not pool or not middleware:
        logger.error(f"User {message.from_user.username} (id={message.from_user.id}) tried to switch roles but missing pool or middleware")
        await message.answer("⚠️ Ошибка конфигурации. Попробуйте позже или обратитесь к администратору.")
        return
        
    try:
        await User.update_role(pool, message.from_user.id, "admin")
        middleware.role_cache[message.from_user.id] = "admin"
        data["role"] = "admin"
        
        logger.info(f"User {message.from_user.username} (id={message.from_user.id}) has switched role to 'admin'")
        await message.answer("✅ Роль изменена на администратора")
        await message.answer(
            text=LEXICON_RU['main'],
            reply_markup=get_admin_menu_markup("main")
        )
    except Exception as e:
        logger.error(f"Error changing role for user {message.from_user.id}: {e}")
        await message.answer("❌ Ошибка при смене роли")

@router.callback_query(NavigationCD.filter())
async def navigate_menu(call: CallbackQuery, callback_data: NavigationCD):
    new_path = callback_data.path
    await call.message.edit_text(
        f"*Вы в меню:* `{new_path}`",
        parse_mode="Markdown",
        reply_markup=get_menu_markup(new_path)
    )