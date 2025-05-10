from typing import Optional

from aiogram.filters.callback_data import CallbackData

from lexicon.lexicon_ru import LEXICON_RU_BUTTONS 

LEXICON = LEXICON_RU_BUTTONS


class NavigationCD(CallbackData, prefix="nav"):
    path: str

class TaskActionCD(CallbackData, prefix="task"):
    action: str
    task_id: Optional[int] = None

class TaskEditCD(CallbackData, prefix="task_edit"):
    field: str
    task_id: int

class TaskEditConfirmCD(CallbackData, prefix="task_edit_confirm"):
    action: str
    task_id: int
    field: str





