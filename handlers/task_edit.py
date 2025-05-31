import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from database.pg_model import Task
from keyboards.admin import get_menu_markup
from states.states import FSMTaskEdit
from handlers.callbacks import NavigationCD, TaskActionCD, TaskEditCD, TaskEditConfirmCD
from filters.roles import IsAdmin
from utils.event_time import EventTime, EventTimeManager

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

def get_day_selection_keyboard(event_manager: EventTimeManager, task_id: int, field: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    current_day = event_manager.get_current_event_day()
    
    for day in range(current_day, event_manager.days_count + 1):
        builder.button(
            text=f"День {day}",
            callback_data=f"edit_day_{field}_{task_id}_{day}"
        )
    
    builder.button(
        text="◀️ Назад",
        callback_data=TaskActionCD(action="view", task_id=task_id).pack()
    )
    
    builder.adjust(2, 1)
    return builder.as_markup()

@router.callback_query(TaskActionCD.filter(F.action == "edit"))
async def edit_task(call: CallbackQuery, callback_data: TaskActionCD, pool, state: FSMContext):
    task = await Task.get_by_id(pool, callback_data.task_id)
    if not task:
        await call.answer("Task not found")
        return

    text = "Выберите поле для редактирования:\n\n"
    text += f"Текущие значения:\n"
    text += f"Название: {task.title}\n"
    text += f"Описание: {task.description}\n"
    text += f"Начало: День {task.start_day} {task.start_time}\n"
    text += f"Конец: День {task.end_day} {task.end_time}\n"

    builder = InlineKeyboardBuilder()
    fields = [
        ("📝 Название", "title"),
        ("📋 Описание", "description"),
        ("🕒 Начало", "start"),
        ("🕕 Конец", "end")
    ]
    
    for button_text, field in fields:
        builder.button(
            text=button_text,
            callback_data=TaskEditCD(field=field, task_id=task.task_id).pack()
        )
    
    builder.button(
        text="◀️ Назад",
        callback_data=TaskActionCD(action="view", task_id=task.task_id).pack()
    )
    
    builder.adjust(2, 1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(TaskEditCD.filter())
async def process_edit_field(call: CallbackQuery, callback_data: TaskEditCD, state: FSMContext, event_manager: EventTimeManager):
    field = callback_data.field
    task_id = callback_data.task_id
    
    # Сохраняем информацию о редактируемом поле
    await state.update_data(edit_field=field, task_id=task_id)
    
    if field in ['start', 'end']:
        await call.message.edit_text(
            f"Выберите день для {field}:",
            reply_markup=get_day_selection_keyboard(event_manager, task_id, field)
        )
    else:
        await state.set_state(FSMTaskEdit.edit_value)
        builder = InlineKeyboardBuilder()
        builder.button(
            text="❌ Отмена",
            callback_data=TaskActionCD(action="view", task_id=task_id).pack()
        )
        await call.message.edit_text(
            f"Введите новое значение для {field}:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(lambda c: c.data.startswith("edit_day_"))
async def process_day_selection(call: CallbackQuery, state: FSMContext):
    _, _, field, task_id, day = call.data.split("_")
    task_id = int(task_id)
    day = int(day)
    
    await state.update_data(selected_day=day)
    await state.set_state(FSMTaskEdit.edit_value)
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=TaskActionCD(action="view", task_id=task_id).pack()
    )
    
    await call.message.edit_text(
        f"Выбран день {day}.\n"
        f"Введите время в формате HH:MM (например, 09:30):",
        reply_markup=builder.as_markup()
    )

@router.message(FSMTaskEdit.edit_value)
async def process_edit_value(message: Message, state: FSMContext, pool, event_manager: EventTimeManager):
    data = await state.get_data()
    field = data['edit_field']
    task_id = data['task_id']
    
    task = await Task.get_by_id(pool, task_id)
    if not task:
        await message.answer("Task not found!")
        await state.clear()
        return

    if field in ['start', 'end']:
        try:
            time = datetime.strptime(message.text, "%H:%M").strftime("%H:%M")
            day = data['selected_day']
            
            # Создаем новый EventTime
            new_event_time = EventTime(day=day, time=time)
            
            # Проверяем валидность времени
            if field == 'start':
                end_event_time = EventTime(day=task.end_day, time=task.end_time)
                if event_manager.to_absolute_time(new_event_time) >= event_manager.to_absolute_time(end_event_time):
                    await message.answer("Время начала должно быть раньше времени окончания!")
                    return
                update_fields = {'start_day': day, 'start_time': time}
            else:  # field == 'end'
                start_event_time = EventTime(day=task.start_day, time=task.start_time)
                if event_manager.to_absolute_time(new_event_time) <= event_manager.to_absolute_time(start_event_time):
                    await message.answer("Время окончания должно быть позже времени начала!")
                    return
                update_fields = {'end_day': day, 'end_time': time}
            
        except ValueError:
            await message.answer("Неверный формат времени! Используйте HH:MM")
            return
    else:
        update_fields = {field: message.text}

    # Обновляем задание
    updated_task = await Task.update(pool, task_id, **update_fields)
    if not updated_task:
        await message.answer("Ошибка при обновлении задания!")
        return

    # Получаем абсолютные времена для отображения
    start_abs, end_abs = updated_task.get_absolute_times(event_manager)
    
    # Отправляем информацию об обновленном задании
    await message.answer(
        f"Задание обновлено!\n\n"
        f"Название: {updated_task.title}\n"
        f"Описание: {updated_task.description}\n"
        f"Начало: День {updated_task.start_day} {updated_task.start_time}\n"
        f"Конец: День {updated_task.end_day} {updated_task.end_time}\n"
        f"Абсолютное время начала: {start_abs.strftime('%Y-%m-%d %H:%M')}\n"
        f"Абсолютное время конца: {end_abs.strftime('%Y-%m-%d %H:%M')}\n"
        f"Статус: {updated_task.status}",
        reply_markup=get_menu_markup("main.tasks")
    )
    await state.clear()