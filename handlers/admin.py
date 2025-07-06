import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from typing import Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from states.states import FSMTaskEdit, FSMSpotTask
from services.spot_cleanup import delete_spot_message
from lexicon.lexicon_ru import LEXICON_RU, LEXICON_RU_BUTTONS
from handlers.callbacks import NavigationCD, TaskActionCD
from keyboards.admin import get_menu_markup, spot_task_keyboard
from keyboards.user import get_menu_markup as user_get_menu_markup
from database.pg_model import User, Task, Assignment, SpotTask, SpotTaskResponse
from filters.roles import IsAdmin
from utils.event_time import EventTimeManager
from utils.formatting import format_task_time

logger = logging.getLogger(__name__)

router = Router()

async def delete_spot_message_safe(bot, chat_id, message_id):
    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramBadRequest as e:
        logger.error(f"Can't delete message {message_id} (chat_id={chat_id}): {e}")
    except Exception as e:
        logger.error(f"Can't delete message {message_id} (chat_id={chat_id}): {e}")

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

# Просмотр заданий

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
        text += f"<i>{format_task_time(task)}</i>\n"
        
        # Add volunteers information
        assignments = await Assignment.get_by_task(pool, task.task_id)
        if assignments:
            text += "👥 Волонтеры:\n"
            for assignment in assignments:
                volunteer = await User.get_by_tg_id(pool, assignment.tg_id)
                text += f"  • {volunteer.name} (@{volunteer.tg_username})\n"
        else:
            text += "❌ Нет назначенных волонтеров\n"
            
        text += "\n---\n\n"

    # Build keyboard with sorted tasks and day selection
    builder = InlineKeyboardBuilder()
    for task in active_tasks:  # Use sorted tasks list
        builder.button(
            text=f"📋 {task.title}",
            callback_data=TaskActionCD(action="view", task_id=task.task_id).pack()
        )
    
    builder.button(
        text=LEXICON_RU_BUTTONS['select_day'],
        callback_data="select_day_for_tasks"
    )
    builder.button(
        text="◀️ Назад",
        callback_data=NavigationCD(path="main.tasks").pack()
    )
    
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(lambda c: c.data.startswith("show_tasks_day_"))
async def show_tasks_by_day(call: CallbackQuery, pool, event_manager: EventTimeManager):
    day = int(call.data.split("_")[-1])
    
    # Get all tasks for the selected day
    tasks = await Task.get_all(pool)
    day_tasks = [task for task in tasks if task.start_day == day or task.end_day == day]
    
    # Sort tasks by start time
    day_tasks.sort(key=lambda x: x.start_time)
    
    text = LEXICON_RU['task_list.day_tasks'].format(day)
    current_time = event_manager.current_time
    
    for task in day_tasks:
        text += f"📌 <b>{task.title}</b>\n"
        text += f"<i>{format_task_time(task)}</i>\n"
        text += f"📝 {task.description}\n"
        
        # Add volunteers information
        assignments = await Assignment.get_by_task(pool, task.task_id)
        if assignments:
            text += "👥 Волонтеры:\n"
            for assignment in assignments:
                volunteer = await User.get_by_tg_id(pool, assignment.tg_id)
                text += f"  • {volunteer.name} (@{volunteer.tg_username})\n"
        else:
            text += "❌ Нет назначенных волонтеров\n"
            
        text += "\n---\n\n"
    
    if not day_tasks:
        text += "На этот день заданий нет."
    
    builder = InlineKeyboardBuilder()
    
    # Add buttons for active tasks
    for task in day_tasks:
        start_abs, end_abs = task.get_absolute_times(event_manager)
        if end_abs > current_time:  # Only add button for active tasks
            builder.button(
                text=f"📋 {task.title}",
                callback_data=TaskActionCD(action="view", task_id=task.task_id).pack()
            )
    
    # Navigation buttons
    builder.button(
        text="📅 Другой день",
        callback_data="select_day_for_tasks"
    )
    builder.button(
        text="◀️ Назад",
        callback_data=NavigationCD(path="main.tasks.list").pack()
    )
    
    # Adjust buttons layout - one task button per row, navigation buttons together
    if day_tasks:
        builder.adjust(1, 2)
    else:
        builder.adjust(2)
    
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
    text += f"Время: {format_task_time(task)}\n\n"

    # Get and display assigned volunteers
    assignments = await Assignment.get_by_task(pool, task.task_id)
    if assignments:
        text += "👥 Назначенные волонтеры:\n"
        for assignment in assignments:
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


# ---- Создание спотов
@router.callback_query(NavigationCD.filter(F.path == "main.tasks.create_spot_task"))
async def start_spot_task_creation(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите название срочного задания:")
    await state.set_state(FSMSpotTask.name)

@router.message(FSMSpotTask.name)
async def process_spot_task_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание срочного задания:")
    await state.set_state(FSMSpotTask.description)

@router.message(FSMSpotTask.description)
async def process_spot_task_description(message: Message, state: FSMContext, pool, bot, spot_duration, debug, scheduler: AsyncIOScheduler):
    data = await state.get_data()
    name = data["name"]
    description = message.text

    expiry_minutes = spot_duration 
    expires_at = datetime.now() + timedelta(minutes=expiry_minutes)

    try:
        spot_task_id = await SpotTask.create(pool, name, description, expires_at)
    except Exception as e:
        logger.error(f"{message.from_user.username} (id={message.from_user.id}): Error while creating spot task: {e}")
        return

    await state.clear()

    # Notify all volunteers
    volunteers = await User.get_by_role(pool, "volunteer")
    msgs = []
    if debug:
        admins = await User.get_by_role(pool, "admin")
        volunteers += admins
    
    for v in volunteers:
        try:
            msg = await bot.send_message(
                v.tg_id,
                f"⚡️ <b>Срочное задание!</b>\n<b>{name}</b>\n{description}",
                reply_markup=spot_task_keyboard(spot_task_id)
            )

            await SpotTaskResponse.create(pool, spot_task_id, v.tg_id, "none", msg.message_id)

            msgs.append(msg)
        except Exception as e:
            logger.error(f"Error sending message to user {v.tg_username} (id={v.tg_id}): {e}")
            await message.answer(f"Срочное задание не отправлено @{v.tg_username}")
        
        try:
            scheduler.add_job(
                delete_spot_message,
                "date",
                run_date=expires_at,
                args=[bot.token, v.tg_id, msg.message_id],
                id=f"spot_task_{spot_task_id}_{v.tg_id}",
                misfire_grace_time=60
            )
        except Exception as e:
            logger.error(f"Error scheduling message deletion to user {v.tg_username} (id={v.tg_id}): {e}")
            

    await message.answer(f"Срочное задание отправлено <b>{len(msgs)}</b> волонтерам.")


# ---- Spot list

@router.callback_query(NavigationCD.filter(F.path == "main.tasks.spot_list"))
async def show_spot_tasks_list(call: CallbackQuery, pool):
    """Показать список срочных (спот) заданий с кнопками"""
    spot_tasks = await SpotTask.get_all(pool)
    if not spot_tasks:
        await call.message.edit_text("Нет срочных заданий.", reply_markup=get_menu_markup("main.tasks"))
        return

    text = "<b>Список срочных заданий:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for spot in spot_tasks:
        text += f"⚡️ <b>{spot.name}</b>\n"
        text += f"📝 {spot.description}\n"
        text += f"⏰ До: {spot.expires_at.strftime('%d.%m %H:%M')}\n"
        text += f"ID: {spot.spot_task_id}\n\n"
        builder.button(
            text=f"{spot.name}",
            callback_data=f"view_spot_{spot.spot_task_id}"
        )
    builder.button(
        text="◀️ Назад",
        callback_data=NavigationCD(path="main.tasks").pack()
    )
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(lambda c: c.data.startswith("view_spot_"))
async def view_spot_task(call: CallbackQuery, pool, scheduler: AsyncIOScheduler, bot):
    spot_task_id = int(call.data.split("_")[-1])
    spot = await SpotTask.get_by_id(pool, spot_task_id)
    if not spot:
        await call.answer("Задание не найдено", show_alert=True)
        return

    # Получаем ответы волонтеров
    responses = await SpotTaskResponse.get_by_task(pool, spot_task_id)
    yes_users = []
    no_users = []
    for resp in responses:
        # Используем правильное имя поля volunteer_id
        user = await User.get_by_tg_id(pool, resp['volunteer_id'])
        if not user:
            continue
        if resp['response'] == "accepted":
            yes_users.append(f"• {user.name} (@{user.tg_username})")
        elif resp['response'] == "declined":
            no_users.append(f"• {user.name} (@{user.tg_username})")

    text = (
        f"⚡️ <b>{spot.name}</b>\n"
        f"📝 {spot.description}\n"
        f"⏰ До: {spot.expires_at.strftime('%d.%m %H:%M')}\n\n"
        f"<b>Откликнулись (+):</b>\n" + ("\n".join(yes_users) if yes_users else "—") + "\n\n"
        f"<b>Отказались (–):</b>\n" + ("\n".join(no_users) if no_users else "—")
    )

    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Закрыть задание",
        callback_data=f"close_spot_{spot_task_id}"
    )
    builder.button(
        text="◀️ Назад",
        callback_data=NavigationCD(path="main.tasks.spot_list").pack()
    )
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(lambda c: c.data.startswith("close_spot_"))
async def close_spot_task(call: CallbackQuery, pool, scheduler: AsyncIOScheduler, bot):
    spot_task_id = int(call.data.split("_")[-1])
    spot = await SpotTask.get_by_id(pool, spot_task_id)
    if not spot:
        await call.answer("Задание не найдено", show_alert=True)
        return

    # Получаем все ответы, чтобы удалить сообщения
    responses = await SpotTaskResponse.get_by_task(pool, spot_task_id)

    # Удаляем сообщения и scheduler jobs
    for resp in responses:
        volunteer_id = resp['volunteer_id']
        message_id = resp.get('message_id')
        if message_id:
            await delete_spot_message_safe(bot, volunteer_id, message_id)
        job_id = f"spot_task_{spot_task_id}_{volunteer_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")

    # Удаляем задание из базы
    await SpotTask.delete(pool, spot_task_id)
    await call.message.edit_text("✅ Срочное задание закрыто и удалено.", reply_markup=get_menu_markup("main.tasks.spot_list"))


@router.callback_query(NavigationCD.filter())
async def navigate_menu(call: CallbackQuery, callback_data: NavigationCD):
    new_path = callback_data.path
    await call.message.edit_text(
        LEXICON_RU[new_path],
        parse_mode="HTML",  # <-- Исправлено!
        reply_markup=get_menu_markup(new_path)
    )


# --- Удаление задания

@router.callback_query(TaskActionCD.filter(F.action == "delete"))
async def confirm_delete_task(call: CallbackQuery, callback_data: TaskActionCD, pool):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=TaskActionCD(action="view", task_id=callback_data.task_id).pack()
    )
    builder.button(
        text="✅ Подтвердить удаление",
        callback_data=f"confirm_delete_{callback_data.task_id}"
    )
    await call.message.edit_text(
        f"Вы уверены, что хотите удалить это задание?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(lambda c: c.data.startswith("confirm_delete_"))
async def delete_task(call: CallbackQuery, pool):
    task_id = int(call.data.split("_")[-1])
    from database.pg_model import Task
    deleted = await Task.delete(pool, task_id)
    if deleted:
        await call.message.edit_text("✅ Задание удалено.")
    else:
        await call.message.edit_text("❌ Ошибка при удалении задания.")

from aiogram.filters import CommandObject
from aiogram.types import Message, Document

@router.message(Command(commands=['import_tasks']))
async def import_tasks_command(message: Message, state: FSMContext):
    await message.answer("Пришлите .csv файл с задачами (первой строкой: title,description,start_day,start_time,end_day,end_time)")
    await state.set_state("awaiting_csv")

@router.message(StateFilter("awaiting_csv"), lambda m: m.document and m.document.mime_type == "text/csv")
async def import_tasks_from_csv(message: Message, pool, state: FSMContext):
    file = await message.bot.get_file(message.document.file_id)
    file_path = file.file_path
    csv_bytes = await message.bot.download_file(file_path)
    csv_content = csv_bytes.read().decode("utf-8")

    await Task.import_from_csv(pool, csv_content)
    await message.answer("✅ Импорт задач завершён.")
    await state.clear()

@router.message(Command(commands=['export_tasks']))
async def export_tasks_to_csv(message: Message, pool):
    csv_content = await Task.export_to_csv(pool)
    await message.answer_document(
        BufferedInputFile(csv_content.encode('utf-8'), filename="tasks_export.csv"),
        caption="Выгрузка задач"
    )


