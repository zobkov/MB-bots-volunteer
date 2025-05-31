import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.pg_model import Task
from keyboards.admin import get_menu_markup
from keyboards.calendar import get_calendar_keyboard
from states.states import FSMTaskEdit
from handlers.callbacks import NavigationCD, TaskActionCD, TaskEditCD, TaskEditConfirmCD
from filters.roles import IsAdmin
from handlers.admin import show_task_details
from lexicon.lexicon_ru import LEXICON_RU

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

@router.callback_query(TaskActionCD.filter(F.action == "edit"))
async def edit_task(call: CallbackQuery, callback_data: TaskActionCD, pool, state: FSMContext):
    task = await Task.get_by_id(pool, callback_data.task_id)
    if not task:
        await call.answer("Task not found")
        logger.error(f"User {call.from_user.username} (id={call.from_user.id}): Task id={callback_data.task_id} is not found in the DB")
        return

    text = "Выберите поле для редактирования:\n\n"
    text += f"Текущие значения:\n"
    text += f"Название: {task.title}\n"
    text += f"Описание: {task.description}\n"
    text += f"Начало: {task.start_ts.strftime('%Y-%m-%d %H:%M')}\n"
    text += f"Конец: {task.end_ts.strftime('%Y-%m-%d %H:%M')}\n"

    builder = InlineKeyboardBuilder()
    fields = [
        ("📝 Название", "title"),
        ("📋 Описание", "description"),
        ("🕒 Начало", "start_ts"),
        ("🕕 Конец", "end_ts")
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
async def process_edit_field(call: CallbackQuery, callback_data: TaskEditCD, state: FSMContext, pool):
    field = callback_data.field
    task_id = callback_data.task_id
    
    task = await Task.get_by_id(pool, task_id)
    if not task:
        await call.answer("Task not found!")
        return
    
    await state.update_data(
        task_id=task_id, 
        field=field,
        current_start=task.start_ts.strftime("%Y-%m-%d %H:%M"),
        current_end=task.end_ts.strftime("%Y-%m-%d %H:%M")
    )
    await state.set_state(FSMTaskEdit.edit_value)
    
    if field in ['start_ts', 'end_ts']:
        await call.message.edit_text(
            f"Выберите новую {field.replace('_ts', '')} дату:",
            reply_markup=get_calendar_keyboard()
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="❌ Отмена",
            callback_data=TaskActionCD(action="view", task_id=task_id).pack()
        )
        builder.adjust(1)
        await call.message.edit_text(
            f"Введите новое значение для {field}:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(lambda c: c.data.startswith(("date_", "month_")), FSMTaskEdit.edit_value)
async def process_calendar_edit_selection(call: CallbackQuery, state: FSMContext):
    if call.data.startswith("month_"):
        new_date = datetime.strptime(call.data[6:], "%Y-%m")
        await call.message.edit_reply_markup(
            reply_markup=get_calendar_keyboard(new_date)
        )
        return
    
    elif call.data.startswith("date_"):
        selected_date = call.data[5:]
        data = await state.get_data()
        field = data['field']
        current_start = datetime.strptime(data['current_start'], "%Y-%m-%d %H:%M")
        current_end = datetime.strptime(data['current_end'], "%Y-%m-%d %H:%M")
        
        selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")
        
        if field == 'start_ts' and selected_datetime.date() > current_end.date():
            builder = InlineKeyboardBuilder()
            builder.button(
                text="📅 Поменять конечную дату",
                callback_data=TaskEditCD(field="end_ts", task_id=data['task_id']).pack()
            )
            builder.button(
                text="🔄 Выбрать другую дату",
                callback_data=TaskEditCD(field="start_ts", task_id=data['task_id']).pack()
            )
            builder.adjust(1)
            await call.message.edit_text(
                f"Ошибка: Дата начала не может быть после даты конца ({current_end.strftime('%Y-%m-%d')})",
                reply_markup=builder.as_markup()
            )
            return
            
        elif field == 'end_ts' and selected_datetime.date() < current_start.date():
            builder = InlineKeyboardBuilder()
            builder.button(
                text="📅 Изменить начальную дату",
                callback_data=TaskEditCD(field="start_ts", task_id=data['task_id']).pack()
            )
            builder.button(
                text="🔄 Выбрать другую дату",
                callback_data=TaskEditCD(field="end_ts", task_id=data['task_id']).pack()
            )
            builder.adjust(1)
            await call.message.edit_text(
                f"Ошибка: Конечная дата не может быть до начальной ({current_start.strftime('%Y-%m-%d')}).",
                reply_markup=builder.as_markup()
            )
            return
        
        await state.update_data(selected_date=selected_date)
        
        builder = InlineKeyboardBuilder()
        builder.button(
            text="❌ Отмена",
            callback_data=TaskActionCD(action="view", task_id=data['task_id']).pack()
        )
        builder.adjust(1)
        await call.message.edit_text(
            f"Выбранная дата: {selected_date}\n"
            f"Укажите время в формате HH:MM (например, 09:30):",
            reply_markup=builder.as_markup()
        )

@router.message(FSMTaskEdit.edit_value)
async def process_edit_value(message: Message, state: FSMContext, pool):
    data = await state.get_data()
    field = data['field']
    task_id = data['task_id']
    
    task = await Task.get_by_id(pool, task_id)
    if not task:
        await message.answer("Task not found!")
        await state.clear()
        return

    if field in ['start_ts', 'end_ts']:
        try:
            selected_date = data.get('selected_date')
            if not selected_date:
                new_datetime = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            else:
                time = datetime.strptime(message.text, "%H:%M").strftime("%H:%M")
                new_value = f"{selected_date} {time}"
                new_datetime = datetime.strptime(new_value, "%Y-%m-%d %H:%M")

            current_start = datetime.strptime(data['current_start'], "%Y-%m-%d %H:%M")
            current_end = datetime.strptime(data['current_end'], "%Y-%m-%d %H:%M")
            
            if field == 'start_ts' and new_datetime >= current_end:
                builder = InlineKeyboardBuilder()
                builder.button(
                    text="📅 Поменять конечное время",
                    callback_data=TaskEditCD(field="end_ts", task_id=task_id).pack()
                )
                builder.button(
                    text="🔄 Выбрать другое время",
                    callback_data=TaskEditCD(field="start_ts", task_id=task_id).pack()
                )
                builder.adjust(1)
                await message.answer(
                    f"Ошибка: Время начала не может быть после времени конца ({current_end.strftime('%Y-%m-%d %H:%M')}).",
                    reply_markup=builder.as_markup()
                )
                return
            
            elif field == 'end_ts' and new_datetime <= current_start:
                builder = InlineKeyboardBuilder()
                builder.button(
                    text="📅 Поменять начальное время",
                    callback_data=TaskEditCD(field="start_ts", task_id=task_id).pack()
                )
                builder.button(
                    text="🔄 Выбрать другое время",
                    callback_data=TaskEditCD(field="end_ts", task_id=task_id).pack()
                )
                builder.adjust(1)
                await message.answer(
                    f"Ошибка: Конечное время не может быть до начального ({current_start.strftime('%Y-%m-%d %H:%M')}).",
                    reply_markup=builder.as_markup()
                )
                return
                
            new_value = new_datetime

        except ValueError:
            builder = InlineKeyboardBuilder()
            builder.button(
                text="📅 Выбрать из календаря",
                callback_data=TaskEditCD(field=field, task_id=task_id).pack()
            )
            builder.button(
                text="❌ Отмена",
                callback_data=TaskActionCD(action="view", task_id=task_id).pack()
            )
            builder.adjust(1)
            await message.answer(
                "Неправильный формат времени. Используйте формат HH:MM (e.g. 09:30) or select from calendar:",
                reply_markup=builder.as_markup()
            )
            return
    else:
        new_value = message.text

    # Add Task.update method to pg_model.py
    await state.update_data(new_value=new_value)
    await state.set_state(FSMTaskEdit.confirm_edit)
    
    text = f"Подтвердите изменение поля {field}:\n"
    text += f"Новое значение: {new_value}"
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=TaskEditConfirmCD(action="confirm", task_id=task_id, field=field).pack()
    )
    builder.button(
        text="❌ Отмена",
        callback_data=TaskEditConfirmCD(action="cancel", task_id=task_id, field=field).pack()
    )
    builder.adjust(2)
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(TaskEditConfirmCD.filter())
async def process_edit_confirmation(call: CallbackQuery, callback_data: TaskEditConfirmCD, state: FSMContext, pool):
    if callback_data.action == "cancel":
        await state.clear()
        await call.message.edit_text("Редактирование отменено")
        await show_task_details(call, TaskActionCD(action="view", task_id=callback_data.task_id), pool)
        return

    data = await state.get_data()
    new_value = data['new_value']
    field = callback_data.field
    task_id = callback_data.task_id

    async with pool.acquire() as conn:
        if field in ['start_ts', 'end_ts']:
            # Handle datetime string that might include seconds
            if isinstance(new_value, str):
                try:
                    # Try parsing with seconds first
                    new_value = datetime.strptime(str(new_value), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        # Try parsing without seconds
                        new_value = datetime.strptime(str(new_value), "%Y-%m-%d %H:%M")
                    except ValueError as e:
                        logger.error(f"Failed to parse datetime: {e}")
                        await call.message.edit_text("Error: Invalid date format")
                        return
        
        await conn.execute(
            f'''
            UPDATE task 
            SET {field} = $1, updated_at = $2
            WHERE task_id = $3
            ''',
            new_value, datetime.now(), task_id
        )

    # Show updated task details
    await call.message.edit_text(f"{field} успешно обновлено!")
    await show_task_details(call, TaskActionCD(action="view", task_id=task_id), pool)
    await state.clear()