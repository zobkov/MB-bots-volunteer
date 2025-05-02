from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from lexicon.lexicon_ru import LEXICON_RU_BUTTONS

from keyboards.buttons_general import go_back, main_menu


assignment_list = InlineKeyboardButton(
    text=LEXICON_RU_BUTTONS['assignment_list'],
    callback_data='admin-assignment_list'
)

task_list = InlineKeyboardButton(
    text=LEXICON_RU_BUTTONS['task_list'],
    callback_data='admin-task_list'
)

keyboard_main_menu = InlineKeyboardMarkup(
    inline_keyboard=[[assignment_list],
                     [task_list]]
)

keyboard_task_list = InlineKeyboardMarkup(
inline_keyboard=[[main_menu, go_back]]
)

keyboard_assignment_list = InlineKeyboardMarkup(
inline_keyboard=[[main_menu, go_back]]
)