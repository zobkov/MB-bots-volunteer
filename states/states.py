from aiogram.fsm.state import State, StatesGroup


class FSMTaskCreation(StatesGroup):
    title = State()
    description = State()
    start_time = State()
    end_time = State()

class FSMTaskEdit(StatesGroup):
    edit_field = State()
    edit_value = State()
    confirm_edit = State()

class FSMStartRole(StatesGroup):
    user = State()
    admin = State()