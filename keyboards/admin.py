from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lexicon.lexicon_ru import LEXICON_RU, LEXICON_RU_BUTTONS

from keyboards.menu_structures import admin_menu_structure as menu_structure
from handlers.callbacks import NavigationCD




def get_menu_markup(path: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопки текущего уровня из словаря
    for label, subpath in menu_structure.get(path, []):
        builder.button(
            text=label,
            callback_data=NavigationCD(path=subpath).pack()
        )

    # Кнопка "Назад" к родителю, если он есть
    if "." in path:
        parent = path.rsplit(".", 1)[0]
        builder.button(
            text=LEXICON_RU_BUTTONS.get("back", "◀️ Назад"),
            callback_data=NavigationCD(path=parent).pack()
        )

    # 2 кнопки в ряд (можно настроить)
    builder.adjust(2)
    return builder.as_markup()

async def send_menu_message(message: Message | CallbackQuery, path: str) -> Message:
    """
    Send a new message with menu instead of editing existing one.
    Works with both Message and CallbackQuery objects.
    Returns the sent message.
    """
    # Get actual Message object if CallbackQuery was passed
    msg = message.message if isinstance(message, CallbackQuery) else message
    
    return await msg.answer(
        text=LEXICON_RU.get(path, f"Меню: {path}"),
        reply_markup=get_menu_markup(path)
    )

def spot_task_keyboard(spot_task_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"spot_accept_{spot_task_id}")
    builder.button(text="❌ Отклонить", callback_data=f"spot_decline_{spot_task_id}")
    builder.adjust(2)
    return builder.as_markup()