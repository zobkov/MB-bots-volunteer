import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from database.pg_model import Task
from keyboards.admin import get_menu_markup
from states.states import FSMTaskCreation
from handlers.callbacks import NavigationCD
from filters.roles import IsAdmin
from lexicon.lexicon_ru import LEXICON_RU
from utils.event_time import EventTime, EventTimeManager

logger = logging.getLogger(__name__)

router = Router()

def get_day_selection_keyboard(event_manager: EventTimeManager) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    current_day = event_manager.get_current_event_day()
    
    for day in range(current_day, event_manager.days_count + 1):
        builder.button(
            text=f"День {day}",
            callback_data=f"day_{day}"
        )
    
    builder.adjust(2)
    return builder.as_markup()

@router.callback_query(NavigationCD.filter(F.path == "main.tasks.create_task"))
async def add_task(call: CallbackQuery, state: FSMContext):
    logger.info(f'{call.from_user.username} (id={call.from_user.id}) has started task creation')
    await call.message.edit_text(LEXICON_RU["task_creation.title"])
    await state.set_state(FSMTaskCreation.title)

@router.message(FSMTaskCreation.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(LEXICON_RU['task_creation.description'])
    await state.set_state(FSMTaskCreation.description)

@router.message(FSMTaskCreation.description)
async def process_description(message: Message, state: FSMContext, event_manager: EventTimeManager):
    await state.update_data(description=message.text)
    
    await message.answer(
        "Выберите день мероприятия для начала задания:",
        reply_markup=get_day_selection_keyboard(event_manager)
    )
    await state.set_state(FSMTaskCreation.start_time)

@router.callback_query(lambda c: c.data.startswith("day_"))
async def process_day_selection(call: CallbackQuery, state: FSMContext):
    day = int(call.data.split("_")[1])
    await state.update_data(start_day=day)
    
    await call.message.edit_text(
        f"Выбран день {day}\n"
        f"Введите время начала в формате HH:MM (например, 09:30):"
    )

@router.message(FSMTaskCreation.start_time)
async def process_start_time(message: Message, state: FSMContext, event_manager: EventTimeManager):
    try:
        # Проверяем формат времени
        time = datetime.strptime(message.text, "%H:%M").strftime("%H:%M")
        data = await state.get_data()
        start_day = data['start_day']
        
        # Создаем EventTime для проверки
        start_event_time = EventTime(day=start_day, time=time)
        
        # Проверяем, что время в будущем
        if not event_manager.is_valid_event_time(start_event_time):
            await message.answer(
                "Выберите будущее время!\n"
                "Выберите день начала заново:",
                reply_markup=get_day_selection_keyboard(event_manager)
            )
            return
            
        await state.update_data(start_time=time)
        
        # Показываем клавиатуру для выбора дня окончания
        await message.answer(
            "Выберите день окончания задания:",
            reply_markup=get_day_selection_keyboard(event_manager)
        )
        await state.set_state(FSMTaskCreation.end_time)
        
    except ValueError:
        await message.answer(LEXICON_RU['task_creation.invalid_time_format'])

@router.message(FSMTaskCreation.end_time)
async def process_end_time(message: Message, state: FSMContext, event_manager: EventTimeManager, pool):
    try:
        time = datetime.strptime(message.text, "%H:%M").strftime("%H:%M")
        data = await state.get_data()
        
        # Создаем объекты EventTime для начала и конца
        start_event_time = EventTime(day=data['start_day'], time=data['start_time'])
        end_event_time = EventTime(day=data['start_day'], time=time)  # Используем тот же день
        
        # Получаем абсолютные времена для сравнения
        start_abs = event_manager.to_absolute_time(start_event_time)
        end_abs = event_manager.to_absolute_time(end_event_time)
        
        if end_abs <= start_abs:
            await message.answer(
                f"Время окончания должно быть после начала ({data['start_time']})!\n"
                f"Введите время окончания заново:"
            )
            return
            
        # Создаем задание
        task = await Task.create(
            pool=pool,
            title=data['title'],
            description=data['description'],
            start_event_time=start_event_time,
            end_event_time=end_event_time
        )
        
        logger.info(f'Task created: id={task.task_id} by user {message.from_user.username} (id={message.from_user.id})')

        # Показываем информацию о созданном задании
        start_abs, end_abs = task.get_absolute_times(event_manager)
        await message.answer(
            f"Задание успешно создано!\n\n"
            f"Название: {task.title}\n"
            f"Описание: {task.description}\n"
            f"Начало: День {task.start_day} {task.start_time}\n"
            f"Конец: День {task.end_day} {task.end_time}\n"
            f"Абсолютное время начала: {start_abs.strftime('%Y-%m-%d %H:%M')}\n"
            f"Абсолютное время конца: {end_abs.strftime('%Y-%m-%d %H:%M')}\n",
            reply_markup=get_menu_markup("main.tasks")
        )
        await state.clear()
        
    except ValueError:
        await message.answer(LEXICON_RU['task_creation.invalid_time_format'])