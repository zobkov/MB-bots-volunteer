from aiogram.fsm.state import State, StatesGroup


class FSMRole(StatesGroup):
    admin = State()
    volunteer = State()
    unauth = State()
    superuser = State()


class FSMTaskCreation(StatesGroup):
    title = State()
    description = State()
    start_time = State()
    end_time = State()
