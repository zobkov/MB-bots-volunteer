import logging

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states.states import FSMTaskEdit

from database.sqlite_model import Task

from lexicon.lexicon_ru import LEXICON_RU 

from handlers.callbacks import NavigationCD, TaskActionCD, TaskEditCD, TaskEditConfirmCD
from keyboards.admin import get_menu_markup
from keyboards.user import get_menu_markup as user_get_menu_markup

from database.sqlite_model import User

from filters.roles import IsAdmin

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

@router.message(CommandStart())
async def proccess_start_admin(message: Message):
    await message.answer(
        text=LEXICON_RU["main"],
        reply_markup=get_menu_markup("main")
    )

@router.message(Command(commands=['change_roles']))
async def role_change_admin_handler(message: Message, conn=None, middleware=None, **data):
    if conn and middleware:
        await User.update_role(conn, message.from_user.id, "volunteer")
        middleware.role_cache[message.from_user.id] = "volunteer"
        data["role"] = "volunteer"
        
        logger.info(f"User {message.from_user.username} (id={message.from_user.id}) has switched role to 'volunteer'")
        await message.answer("Роль изменена на волонтера")
        await message.answer(
            text=LEXICON_RU["main"],  
            reply_markup=user_get_menu_markup("main")
        )
    else:
        logger.error(f"User {message.from_user.username} (id={message.from_user.id}) tried to switch roles but missing connection or middleware")
        await message.answer("Configuration error")

@router.callback_query(NavigationCD.filter(F.path == "main.tasks.list"))
async def show_tasks_list(call: CallbackQuery, conn):
    current_time = datetime.now()
    tasks = await Task.get_all(conn)
    active_tasks = [task for task in tasks if task.end_ts > current_time]
    
    text = "Текущие активные задания:\n\n"
    for task in active_tasks:
        text += f"📌 {task.title}\n"
        text += f"Начало: {task.start_ts.strftime('%Y-%m-%d %H:%M')}\n"
        text += f"Конец: {task.end_ts.strftime('%Y-%m-%d %H:%M')}\n\n"

    builder = InlineKeyboardBuilder()
    for task in active_tasks:
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



@router.callback_query(TaskActionCD.filter(F.action == "delete"))
async def edit_task(call: CallbackQuery, callback_data: TaskActionCD, conn):
    NotImplemented # TODO

@router.callback_query(TaskActionCD.filter(F.action == "create_assignment"))
async def edit_task(call: CallbackQuery, callback_data: TaskActionCD, conn):
    NotImplemented # TODO

@router.callback_query(TaskActionCD.filter(F.action == "view"))
async def show_task_details(call: CallbackQuery, callback_data: TaskActionCD, conn):
    task = await Task.get_by_id(conn, callback_data.task_id)
    if not task:
        await call.answer("Task not found!")
        return
    
    text = f"📋 Детали задания:\n\n"
    text += f"Название: {task.title}\n"
    text += f"Описание: {task.description}\n"
    text += f"Начало: {task.start_ts.strftime('%Y-%m-%d %H:%M')}\n"
    text += f"Конец: {task.end_ts.strftime('%Y-%m-%d %H:%M')}\n"
    text += f"Статус: {task.status}\n"

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
    await call.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(NavigationCD.filter())
async def navigate_menu(call: CallbackQuery, callback_data: NavigationCD):
    new_path = callback_data.path
    await call.message.edit_text(
        LEXICON_RU[new_path],
        parse_mode="Markdown",
        reply_markup=get_menu_markup(new_path)
    )