import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.pg_model import Task
from keyboards.admin import get_menu_markup
from keyboards.calendar import get_calendar_keyboard
from states.states import FSMTaskCreation
from handlers.callbacks import NavigationCD
from filters.roles import IsAdmin
from lexicon.lexicon_ru import LEXICON_RU

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

@router.callback_query(NavigationCD.filter(F.path == "main.tasks.create_task"))
async def add_task(call: CallbackQuery, state: FSMContext):
    logger.info(f'{call.message.from_user.username} (id={call.message.from_user.id}) has started add_task() handler')
    await call.message.edit_text(LEXICON_RU["task_creation.title"])
    await state.set_state(FSMTaskCreation.title)

@router.message(FSMTaskCreation.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(LEXICON_RU['task_creation.description'])
    await state.set_state(FSMTaskCreation.description)

@router.message(FSMTaskCreation.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        LEXICON_RU['task_creation.start_date'],
        reply_markup=get_calendar_keyboard()
    )
    await state.set_state(FSMTaskCreation.start_time)

@router.callback_query(lambda c: c.data.startswith(("date_", "month_")))
async def process_calendar_selection(call: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    
    if call.data.startswith("month_"):
        # Handle month navigation
        new_date = datetime.strptime(call.data[6:], "%Y-%m")
        await call.message.edit_reply_markup(
            reply_markup=get_calendar_keyboard(new_date)
        )
        return
    
    elif call.data.startswith("date_"):
        selected_date = call.data[5:]
        
        if current_state == FSMTaskCreation.end_time:
            data = await state.get_data()
            start_datetime = datetime.strptime(data['start_time'], "%Y-%m-%d %H:%M")
            selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")
            
            if selected_datetime.date() < start_datetime.date():
                await call.message.edit_text(
                    f"Конченая дата дожна быть после {start_datetime.strftime('%Y-%m-%d')}!\n"
                    f"Пожалуйста, укажите правильную дату:",
                    reply_markup=get_calendar_keyboard(selected_datetime)
                )
                logger.warning(f'{call.message.from_user.username} (id={call.message.from_user.id}): Invalid date. Must be not before the start date')
                return
        
        await state.update_data(selected_date=selected_date)
        await call.message.edit_text(
            f"Выбранная дата: {selected_date}\n"
            f"{LEXICON_RU['task_creation.time_format']}"
        )

@router.message(FSMTaskCreation.start_time)
async def process_time_input(message: Message, state: FSMContext):
    try:
        time = datetime.strptime(message.text, "%H:%M").strftime("%H:%M")
        data = await state.get_data()
        selected_date = data.get("selected_date")
        
        full_datetime = f"{selected_date} {time}"
        datetime_obj = datetime.strptime(full_datetime, "%Y-%m-%d %H:%M")
        
        if datetime_obj <= datetime.now():
            await message.answer(
                "Выберите будущее время\n"
                "Выберите дату еще раз:",
                reply_markup=get_calendar_keyboard()
            )
            return
            
        await state.update_data(start_time=full_datetime)
        await message.answer(
            LEXICON_RU['task_creation.start_date'],
            reply_markup=get_calendar_keyboard(datetime_obj)
        )
        await state.set_state(FSMTaskCreation.end_time)
        
    except ValueError:
        await message.answer(
            LEXICON_RU['task_creation.invalid_time_format']
        )
        logger.warning(f'{message.from_user.username} (id={message.from_user.id}): Invalid time string')

@router.message(FSMTaskCreation.end_time)
async def process_end_time_input(message: Message, state: FSMContext, pool):
    try:
        time = datetime.strptime(message.text, "%H:%M").strftime("%H:%M")
        data = await state.get_data()
        selected_date = data.get("selected_date")
        start_time = datetime.strptime(data.get("start_time"), "%Y-%m-%d %H:%M")
        
        full_datetime = f"{selected_date} {time}"
        end_time = datetime.strptime(full_datetime, "%Y-%m-%d %H:%M")
        
        if end_time <= start_time:
            await message.answer(
                f"End time must be after {start_time.strftime('%H:%M')} on {start_time.strftime('%Y-%m-%d')}!\n"
                f"Please enter a later time for {selected_date}:"
            )
            return
            
        task = await Task.create(
            pool=pool,
            title=data['title'],
            description=data['description'],
            start_ts=data['start_time'],  # This will be converted to datetime in Task.create
            end_ts=full_datetime,         # This will be converted to datetime in Task.create
            status='Unscheduled'
        )
        
        logger.info(f'{message.from_user.username} (id={message.from_user.id}): Successfully created task id={task.task_id}')

        await message.answer(
            f"Task created successfully!\n\n"
            f"Title: {task.title}\n"
            f"Description: {task.description}\n"
            f"Start: {task.start_ts.strftime('%Y-%m-%d %H:%M')}\n"
            f"End: {task.end_ts.strftime('%Y-%m-%d %H:%M')}\n"
            f"Status: {task.status}",
            reply_markup=get_menu_markup("main.tasks")
        )
        await state.clear()
        
    except ValueError as e:
        logger.error(f"Date parsing error: {e}")
        await message.answer(LEXICON_RU['task_creation.invalid_time_format'])