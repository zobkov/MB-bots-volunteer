from aiogram.fsm.state import State, StatesGroup


class FSMTaskCreation(StatesGroup):
    title = State()
    description = State()
    start_time = State()
    end_time = State()

class FSMTaskEdit(StatesGroup):
    edit_value = State()

class FSMStartRole(StatesGroup):
    user = State()
    admin = State()

class FSMSpotTask(StatesGroup):
    name = State()
    description = State()