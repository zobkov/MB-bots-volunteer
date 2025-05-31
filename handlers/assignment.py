import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup 
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from handlers.callbacks import TaskActionCD
from handlers.admin import show_task_details
from services.assignment_service import AssignmentService
from filters.roles import IsAdmin
from database.pg_model import Task, Assignment, User
from utils.event_time import EventTimeManager, EventTime

from typing import List

from datetime import timedelta

from lexicon.lexicon_ru import LEXICON_RU
from aiogram.exceptions import TelegramNetworkError
import asyncio

from services.notifications import notify_task_volunteers

logger = logging.getLogger(__name__)

router = Router()
router.callback_query.filter(IsAdmin())

class AssignmentStates(StatesGroup):
    selecting_volunteers = State()
    confirming = State()

def get_volunteers_keyboard(volunteers: list, total: int, page: int = 1, per_page: int = 5, selected_ids: list = None):
    builder = InlineKeyboardBuilder()
    selected_ids = selected_ids or []

    for volunteer in volunteers:
        # Add checkmark if volunteer is selected
        mark = "✅ " if volunteer.tg_id in selected_ids else ""
        builder.button(
            text=f"{mark}{volunteer.name} (@{volunteer.tg_username})",
            callback_data=f"select_volunteer_{volunteer.tg_id}"
        )

    # Add pagination buttons if needed
    if total > per_page:
        buttons = []
        if page > 1:
            buttons.append(("⬅️", f"vol_page_{page-1}"))
        if page * per_page < total:
            buttons.append(("➡️", f"vol_page_{page+1}"))
        for text, callback_data in buttons:
            builder.button(text=text, callback_data=callback_data)

    # Add control buttons
    builder.button(
        text="✅ Завершить выбор",
        callback_data="finish_selection"
    )
    builder.button(
        text="❌ Отмена",
        callback_data="cancel_selection"
    )

    builder.adjust(1)  # One button per row for better readability
    return builder.as_markup()

def get_assignments_list_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ Создать назначение",
        callback_data="create_new_assignment"
    )
    builder.button(
        text="🔙 Назад",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(TaskActionCD.filter(F.action == "create_assignment"))
async def start_assignment_creation(call: CallbackQuery, callback_data: TaskActionCD, state: FSMContext, pool):
    service = AssignmentService(call.bot, pool)
    volunteers, total = await service.get_volunteers()
    
    # Store task_id and initialize selected volunteers list
    await state.update_data(
        task_id=callback_data.task_id,
        selected_volunteers=[],
        current_page=1
    )
    
    await call.message.edit_text(
        "Выберите волонтеров для назначения:",
        reply_markup=get_volunteers_keyboard(volunteers, total)
    )
    await state.set_state(AssignmentStates.selecting_volunteers)

@router.callback_query(lambda c: c.data.startswith("select_volunteer_"))
async def process_volunteer_selection(call: CallbackQuery, state: FSMContext, pool):
    volunteer_id = int(call.data.split("_")[2])
    data = await state.get_data()
    selected = data.get("selected_volunteers", [])
    current_page = data.get("current_page", 1)
    
    # Toggle volunteer selection
    if volunteer_id in selected:
        selected.remove(volunteer_id)
    else:
        selected.append(volunteer_id)
    
    await state.update_data(selected_volunteers=selected)
    
    # Refresh volunteer list
    service = AssignmentService(call.bot, pool)
    volunteers, total = await service.get_volunteers(page=current_page)
    
    await call.message.edit_reply_markup(
        reply_markup=get_volunteers_keyboard(
            volunteers, total, current_page, selected_ids=selected
        )
    )

@router.callback_query(lambda c: c.data.startswith("vol_page_"))
async def process_page_change(call: CallbackQuery, state: FSMContext, pool):
    page = int(call.data.split("_")[2])
    data = await state.get_data()
    selected = data.get("selected_volunteers", [])
    
    service = AssignmentService(call.bot, pool)
    volunteers, total = await service.get_volunteers(page=page)
    
    await state.update_data(current_page=page)
    await call.message.edit_reply_markup(
        reply_markup=get_volunteers_keyboard(
            volunteers, total, page, selected_ids=selected
        )
    )

@router.callback_query(lambda c: c.data == "finish_selection")
async def finish_volunteer_selection(
    call: CallbackQuery, 
    state: FSMContext, 
    pool, 
    event_manager: EventTimeManager,
    scheduler: AsyncIOScheduler
):
    data = await state.get_data()
    selected = data.get("selected_volunteers", [])
    task_id = data.get("task_id")
    
    if not selected:
        await call.answer("Выберите хотя бы одного волонтера!", show_alert=True)
        return
    
    service = AssignmentService(call.bot, pool)
    try:
        # Check for existing assignments
        existing_assignments = await Assignment.get_by_task(pool, task_id)
        
        if existing_assignments:
            # Cancel existing notifications
            for assignment in existing_assignments:
                job_id = f'notification_task_{task_id}_assignment_{assignment.assign_id}'
                try:
                    scheduler.remove_job(job_id)
                except:
                    pass
                # Update assignment status to 'cancelled'
                await Assignment.update_status(pool, assignment.assign_id, 'cancelled')
            
            # Notify about update
            await call.message.answer(
                f"🔄 Обновляем существующие назначения для задания..."
            )
        
        # Create new assignments
        assignments = await service.create_assignment(
            task_id=task_id,
            volunteer_ids=selected,
            admin_id=call.from_user.id
        )
        
        # Send success message
        await call.message.answer(
            f"✅ {'Обновлено' if existing_assignments else 'Создано'} назначение для {len(assignments)} волонтеров!"
        )
        
        # Send notification setup message
        notification_msg = await call.message.answer(
            "⚙️ Настраиваю уведомления..."
        )

        # Schedule notifications
        task = await Task.get_by_id(pool, task_id)
        start_time = event_manager.to_absolute_time(
            EventTime(day=task.start_day, time=task.start_time)
        )
        notification_time = start_time - timedelta(minutes=5)

        # Get database config from pool
        db_config = {
            'user': pool._connect_kwargs['user'],
            'password': pool._connect_kwargs['password'],
            'database': pool._connect_kwargs['database'],
            'host': pool._connect_kwargs['host'],
            'port': pool._connect_kwargs['port']
        }
        
        # Schedule notifications with unique IDs for each assignment
        for assignment in assignments:
            job_id = f'notification_task_{task_id}_assignment_{assignment.assign_id}'
            scheduler.add_job(
                'services.notifications:notify_task_volunteers',
                'date',
                run_date=notification_time,
                args=[task_id, call.bot.token, db_config],
                id=job_id,
                replace_existing=True
            )
            await Assignment.mark_notification_scheduled(pool, assignment.assign_id)
        
        await notification_msg.edit_text(
            "✅ Уведомления настроены успешно!"
        )
        
        # Show task details with correct parameters
        await show_task_details(
            call=call,  # Pass the whole callback query
            callback_data=TaskActionCD(action="view", task_id=task_id),  # Create proper callback data
            pool=pool
        )
        
    except Exception as e:
        logger.error(f"Error creating assignment: {e}")
        await call.message.answer("❌ Ошибка при создании назначения")
    
    await state.clear()

@router.callback_query(lambda c: c.data == "cancel_selection")
async def cancel_selection(call: CallbackQuery, state: FSMContext, pool):
    await call.message.edit_text("❌ Создание назначения отменено")
    await state.clear()
    
    # Return to task view with correct parameters
    task_id = (await state.get_data()).get('task_id')
    if task_id:
        task = await Task.get_by_id(pool, task_id)
        await show_task_details(
            call=call,  # Pass the whole callback query
            callback_data=TaskActionCD(action="view", task_id=task_id),  # Create proper callback data
            pool=pool
        )

@router.callback_query(lambda c: c.data == "show_assignments_list")
async def show_assignments_list(call: CallbackQuery, pool):
    """Show list of all assignments grouped by tasks"""
    assignments = await Assignment.get_all_with_details(pool)
    
    # Group assignments by task
    tasks_assignments = {}
    for assignment in assignments:
        if assignment.task_id not in tasks_assignments:
            tasks_assignments[assignment.task_id] = []
        tasks_assignments[assignment.task_id].append(assignment)
    
    text = "📋 Список назначений:\n\n"
    for task_id, task_assignments in tasks_assignments.items():
        task = await Task.get_by_id(pool, task_id)
        text += f"🔹 {task.title}\n"
        text += f"   📅 День {task.start_day} {task.start_time} - День {task.end_day} {task.end_time}\n"
        
        for assignment in task_assignments:
            volunteer = await User.get_by_tg_id(pool, assignment.tg_id)
            text += f"   👤 {volunteer.name} (@{volunteer.tg_username})\n"
        text += "\n"
    
    await call.message.edit_text(
        text,
        reply_markup=get_assignments_list_keyboard()
    )

@router.callback_query(lambda c: c.data == "create_new_assignment")
async def start_assignment_creation_flow(call: CallbackQuery, state: FSMContext, pool):
    """Start flow for creating new assignment by showing task list first"""
    tasks = await Task.get_all(pool)
    
    text = "📋 Выберите задание для назначения:\n\n"
    for task in tasks:
        text += (f"🔹 {task.title}\n"
                f"   📅 День {task.start_day} {task.start_time} - "
                f"День {task.end_day} {task.end_time}\n\n")
    
    builder = InlineKeyboardBuilder()
    for task in tasks:
        builder.button(
            text=task.title,
            callback_data=TaskActionCD(action="create_assignment", task_id=task.task_id).pack()
        )
    builder.button(text="🔙 Назад", callback_data="show_assignments_list")
    builder.adjust(1)
    
    await call.message.edit_text(
        text,
        reply_markup=builder.as_markup()
    )