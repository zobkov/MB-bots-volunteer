from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from lexicon.lexicon_ru import LEXICON_RU_BUTTONS


go_back = InlineKeyboardButton(
    text=LEXICON_RU_BUTTONS['go_back'],
    callback_data='general-go_back'
)

main_menu = InlineKeyboardButton(
    text=LEXICON_RU_BUTTONS['main_menu'],
    callback_data='general-main_menu'
)
