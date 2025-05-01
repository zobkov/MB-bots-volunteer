from aiogram.fsm.state import State, StatesGroup


class FSMRole(StatesGroup):
    admin = State()
    volunteer = State()
    unauth = State()
    superuser = State()
