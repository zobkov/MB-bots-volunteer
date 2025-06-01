import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from typing import Union

from states.states import FSMTaskEdit
from lexicon.lexicon_ru import LEXICON_RU 
from handlers.callbacks import NavigationCD, TaskActionCD
from keyboards.admin import get_menu_markup
from keyboards.user import get_menu_markup as user_get_menu_markup
from database.pg_model import User, Task, Assignment
from filters.roles import IsAdmin
from utils.event_time import EventTimeManager

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
async def proccess_start_admin(message: Message):
    await message.answer(
        text=LEXICON_RU["main"],
        reply_markup=get_menu_markup("main")
    )

@router.message(Command(commands=['change_roles']))
async def role_change_admin_handler(message: Message, pool=None, middleware=None, **data):
    if not pool or not middleware:
        logger.error(f"User {message.from_user.username} (id={message.from_user.id}) tried to switch roles but missing pool or middleware")
        await message.answer("⚠️ Ошибка конфигурации. Попробуйте позже или обратитесь к администратору.")
        return
        
    try:
        await User.update_role(pool, message.from_user.id, "volunteer")
        middleware.role_cache[message.from_user.id] = "volunteer"
        data["role"] = "volunteer"
        
        logger.info(f"User {message.from_user.username} (id={message.from_user.id}) has switched role to 'volunteer'")
        await message.answer("✅ Роль изменена на волонтера")
        await message.answer(
            text=LEXICON_RU["main"],  
            reply_markup=user_get_menu_markup("main")
        )
    except Exception as e:
        logger.error(f"Error changing role for user {message.from_user.id}: {e}")
        await message.answer("❌ Ошибка при смене роли")

@router.callback_query(NavigationCD.filter(F.path == "main.tasks.list"))
async def show_tasks_list(call: CallbackQuery, pool, event_manager: EventTimeManager):
    tasks = await Task.get_all(pool)
    current_time = event_manager.current_time
    
    # Convert tasks to tuples of (task, start_time) for sorting
    task_times = []
    for task in tasks:
        start_abs, end_abs = task.get_absolute_times(event_manager)
        if end_abs > current_time:  # Only include active tasks
            task_times.append((task, start_abs))
    
    # Sort tasks by start time
    task_times.sort(key=lambda x: x[1])  # Sort by start_abs
    active_tasks = [task for task, _ in task_times]  # Store sorted tasks for keyboard
    
    text = "<b>Текущие активные задания:</b>\n\n"
    
    for task, start_time in task_times:
        text += f"📌 <b>{task.title}</b>\n"
        text += f"<i>День {task.start_day} {task.start_time} - День {task.end_day} {task.end_time}</i>\n"
        
        # Add volunteers information
        assignments = await Assignment.get_by_task(pool, task.task_id)
        active_assignments = [a for a in assignments if a.status != 'cancelled']
        
        if active_assignments:
            text += "👥 Волонтеры:\n"
            for assignment in active_assignments:
                volunteer = await User.get_by_tg_id(pool, assignment.tg_id)
                text += f"  • {volunteer.name} (@{volunteer.tg_username})\n"
        else:
            text += "❌ Нет назначенных волонтеров\n"
            
        text += "\n---\n\n"

    # Build keyboard with sorted tasks
    builder = InlineKeyboardBuilder()
    for task in active_tasks:  # Use sorted tasks list
        builder.button(
            text=f"📋 {task.title}",
            callback_data=TaskActionCD(action="view", task_id=task.task_id).pack()
        )
    
    builder.button(
        text="◀️ Назад",
        callback_data=NavigationCD(path="main.tasks").pack()
    )
    
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(TaskActionCD.filter(F.action == "view"))
async def show_task_details(update: Union[Message, CallbackQuery], callback_data: TaskActionCD, pool):
    """Show task details, works with both Message and CallbackQuery"""
    task = await Task.get_by_id(pool, callback_data.task_id)
    if not task:
        if isinstance(update, CallbackQuery):
            await update.answer("Task not found!")
        else:
            await update.answer("Task not found!")
        return
    
    text = f"📋 Детали задания:\n\n"
    text += f"Название: {task.title}\n"
    text += f"Описание: {task.description}\n"
    text += f"Начало: День {task.start_day} {task.start_time}\n"
    text += f"Конец: День {task.end_day} {task.end_time}\n"
    text += f"Статус: {task.status}\n\n"

    # Get and display assigned volunteers
    assignments = await Assignment.get_by_task(pool, task.task_id)
    if assignments:
        text += "👥 Назначенные волонтеры:\n"
        for assignment in assignments:
            if assignment.status != 'cancelled':  # Show only active assignments
                volunteer = await User.get_by_tg_id(pool, assignment.tg_id)
                text += f"• {volunteer.name} (@{volunteer.tg_username})\n"
                text += f"  🕒 {assignment.start_time}-{assignment.end_time}\n"
    else:
        text += "❌ Нет назначенных волонтеров\n"

    builder = InlineKeyboardBuilder()
    builder.button(
        text="✏️ Редактировать",
        callback_data=TaskActionCD(action="edit", task_id=task.task_id).pack()
    )
    builder.button(
        text="🗑 Удалить",
        callback_data=TaskActionCD(action="delete", task_id=task.task_id).pack()
    )
    builder.button(
        text="📝 Создать назначение",
        callback_data=TaskActionCD(action="create_assignment", task_id=task.task_id).pack()
    )
    builder.button(
        text="◀️ Назад",
        callback_data=NavigationCD(path="main.tasks.list").pack()
    )
    
    builder.adjust(2, 1, 1)

    # Handle different update types
    if isinstance(update, CallbackQuery):
        await update.message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await update.answer(text, reply_markup=builder.as_markup())

@router.callback_query(NavigationCD.filter())
async def navigate_menu(call: CallbackQuery, callback_data: NavigationCD):
    new_path = callback_data.path
    await call.message.edit_text(
        LEXICON_RU[new_path],
        parse_mode="Markdown",
        reply_markup=get_menu_markup(new_path)
    )