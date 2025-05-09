from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lexicon.lexicon_ru import LEXICON_RU_BUTTONS

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