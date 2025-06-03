from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.callbacks import NavigationCD
from database.pg_model import User, PendingUser, Assignment, Task
from lexicon.lexicon_ru import LEXICON_RU_BUTTONS as LEXICON, LEXICON_VOLUNTEER_RU
from filters.roles import IsAdmin

router = Router()

class AddVolunteerStates(StatesGroup):
    waiting_username = State()
    waiting_name = State()
    confirming = State()

@router.callback_query(NavigationCD.filter(F.path == "main.volunteers.add_volunteer"))
async def start_add_volunteer(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddVolunteerStates.waiting_username)
    await call.message.edit_text(LEXICON_VOLUNTEER_RU['add.username'])

@router.message(StateFilter(AddVolunteerStates.waiting_username))
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")
    await state.update_data(username=username)
    await state.set_state(AddVolunteerStates.waiting_name)
    await message.answer(LEXICON_VOLUNTEER_RU['add.name'])

@router.message(StateFilter(AddVolunteerStates.waiting_name))
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    username = data['username']
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_add_volunteer")
    builder.button(text="❌ Отмена", callback_data="cancel_add_volunteer")
    builder.adjust(2)
    
    await state.update_data(name=name)
    await state.set_state(AddVolunteerStates.confirming)
    await message.answer(
        LEXICON_VOLUNTEER_RU['add.confirm'].format(username, name),
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "confirm_add_volunteer", StateFilter(AddVolunteerStates.confirming))
async def confirm_add_volunteer(call: CallbackQuery, state: FSMContext, pool):
    data = await state.get_data()
    
    try:
        await PendingUser.create(
            pool=pool,
            tg_username=data['username'],
            name=data['name'],
            role='volunteer'
        )
        await call.message.edit_text(LEXICON_VOLUNTEER_RU['add.success'])
    except Exception as e:
        await call.message.edit_text(f"Ошибка при добавлении волонтера: {str(e)}")
    
    await state.clear()

@router.callback_query(F.data == "cancel_add_volunteer")
async def cancel_add_volunteer(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(LEXICON['volunteer.add.cancel'])

@router.callback_query(NavigationCD.filter(F.path == "main.volunteers.list.active"))
async def show_active_volunteers(call: CallbackQuery, pool):
    volunteers = await User.get_by_role(pool, role='volunteer')
    if not volunteers:
        text = LEXICON_VOLUNTEER_RU['list.empty']
    else:
        # Создаем текст для каждого волонтера с его заданиями
        volunteer_sections = []
        for vol in volunteers:
            # Получаем все активные назначения волонтера
            assignments = await Assignment.get_by_volunteer(pool, vol.tg_id)
            active_assignments = [a for a in assignments if a.status != 'cancelled']
            
            # Формируем секцию для волонтера
            section = [f"• {vol.name} (@{vol.tg_username})"]
            
            if active_assignments:
                for assignment in active_assignments:
                    # Получаем информацию о задании
                    task = await Task.get_by_id(pool, assignment.task_id)
                    if task:
                        # Форматируем время
                        time_str = (f"День {assignment.start_day} {assignment.start_time} - "
                                  f"День {assignment.end_day} {assignment.end_time}" 
                                  if assignment.start_day != assignment.end_day else
                                  f"День {assignment.start_day} {assignment.start_time} - {assignment.end_time}")
                        
                        section.append(f"  📋 {task.title} - {time_str}")
            
            volunteer_sections.append("\n".join(section))
        
        # Объединяем все секции в один текст
        text = LEXICON_VOLUNTEER_RU['list.active'].format(
            volunteers="\n\n".join(volunteer_sections)
        )
    
    builder = InlineKeyboardBuilder()
    builder.button(text=LEXICON['go_back'], callback_data=NavigationCD(path="main.volunteers.list").pack())
    
    await call.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(NavigationCD.filter(F.path == "main.volunteers.list.pending"))
async def show_pending_volunteers(call: CallbackQuery, pool):
    volunteers = await PendingUser.get_all(pool)
    if not volunteers:
        text = LEXICON_VOLUNTEER_RU['list.empty']
    else:
        volunteers_text = "\n".join(f"• {vol.name} (@{vol.tg_username})" for vol in volunteers)
        text = LEXICON_VOLUNTEER_RU['list.pending'].format(volunteers=volunteers_text)
    
    builder = InlineKeyboardBuilder()
    builder.button(text=LEXICON['go_back'], callback_data=NavigationCD(path="main.volunteers.list").pack())
    
    await call.message.edit_text(text, reply_markup=builder.as_markup())