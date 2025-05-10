import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.sqlite_model import Task
from keyboards.admin import get_menu_markup
from keyboards.calendar import get_calendar_keyboard
from states.states import FSMTaskCreation
from handlers.callbacks import NavigationCD, TaskActionCD, TaskEditCD, TaskEditConfirmCD
from filters.roles import IsAdmin

from states.states import FSMTaskEdit

from handlers.admin import show_task_details

from lexicon.lexicon_ru import LEXICON_RU

logger = logging.getLogger(__name__)

# Create router specifically for task creation
router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

@router.callback_query(TaskActionCD.filter(F.action == "edit"))
async def edit_task(call: CallbackQuery, callback_data: TaskActionCD, conn, state: FSMContext):
    task = await Task.get_by_id(conn, callback_data.task_id)
    if not task:
        await call.answer("Task not found")
        logger.error(f"User {call.from_user.username} (id={call.from_user.id}): Task id={callback_data.task_id} is not found in the DB")
        return

    text = "Select field to edit:\n\n"
    text += f"Current values:\n"
    text += f"Title: {task.title}\n"
    text += f"Description: {task.description}\n"
    text += f"Start: {task.start_ts.strftime('%Y-%m-%d %H:%M')}\n"
    text += f"End: {task.end_ts.strftime('%Y-%m-%d %H:%M')}\n"

    builder = InlineKeyboardBuilder()
    fields = [
        ("📝 Title", "title"),
        ("📋 Description", "description"),
        ("🕒 Start Time", "start_ts"),
        ("🕕 End Time", "end_ts")
    ]
    
    for button_text, field in fields:
        builder.button(
            text=button_text,
            callback_data=TaskEditCD(field=field, task_id=task.task_id).pack()
        )
    
    builder.button(
        text="◀️ Back",
        callback_data=TaskActionCD(action="view", task_id=task.task_id).pack()
    )
    
    builder.adjust(2, 1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(TaskEditCD.filter())
async def process_edit_field(call: CallbackQuery, callback_data: TaskEditCD, state: FSMContext, conn):
    field = callback_data.field
    task_id = callback_data.task_id
    
    task = await Task.get_by_id(conn, task_id)
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
    
    builder = InlineKeyboardBuilder()
    if field in ['start_ts', 'end_ts']:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="❌ Cancel",
            callback_data=TaskActionCD(action="view", task_id=task_id).pack()
        )
        builder.adjust(1)
        await call.message.edit_text(
            f"Select new {field.replace('_ts', '')} date:",
            reply_markup=get_calendar_keyboard()
        )
    else:
        builder.button(
            text="❌ Cancel",
            callback_data=TaskActionCD(action="view", task_id=task_id).pack()
        )
        builder.adjust(1)
        await call.message.edit_text(
            f"Enter new {field}:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(lambda c: c.data.startswith(("date_", "month_")), FSMTaskEdit.edit_value)
async def process_calendar_edit_selection(call: CallbackQuery, state: FSMContext):
    if call.data.startswith("month_"):
        # Handle month navigation
        new_date = datetime.strptime(call.data[6:], "%Y-%m")
        await call.message.edit_reply_markup(
            reply_markup=get_calendar_keyboard(new_date)
        )
        return
    
    elif call.data.startswith("date_"):
        selected_date = call.data[5:]  # Get the date part
        data = await state.get_data()
        field = data['field']
        current_start = datetime.strptime(data['current_start'], "%Y-%m-%d %H:%M")
        current_end = datetime.strptime(data['current_end'], "%Y-%m-%d %H:%M")
        
        # Validate selected date for start_ts and end_ts
        selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")
        
        if field == 'start_ts' and selected_datetime.date() > current_end.date():
            builder = InlineKeyboardBuilder()
            builder.button(
                text="📅 Change End Time Instead",
                callback_data=TaskEditCD(field="end_ts", task_id=data['task_id']).pack()
            )
            builder.button(
                text="🔄 Select Different Date",
                callback_data=TaskEditCD(field="start_ts", task_id=data['task_id']).pack()
            )
            builder.button(
                text="❌ Cancel",
                callback_data=TaskActionCD(action="view", task_id=data['task_id']).pack()
            )
            builder.adjust(1)
            await call.message.edit_text(
                f"Error: Start date cannot be after end date ({current_end.strftime('%Y-%m-%d')}).\n"
                f"Please choose:",
                reply_markup=builder.as_markup()
            )
            return
            
        elif field == 'end_ts' and selected_datetime.date() < current_start.date():
            builder = InlineKeyboardBuilder()
            builder.button(
                text="📅 Change Start Time Instead",
                callback_data=TaskEditCD(field="start_ts", task_id=data['task_id']).pack()
            )
            builder.button(
                text="🔄 Select Different Date",
                callback_data=TaskEditCD(field="end_ts", task_id=data['task_id']).pack()
            )
            builder.button(
                text="❌ Cancel",
                callback_data=TaskActionCD(action="view", task_id=data['task_id']).pack()
            )
            builder.adjust(1)
            await call.message.edit_text(
                f"Error: End date cannot be before start date ({current_start.strftime('%Y-%m-%d')}).\n"
                f"Please choose:",
                reply_markup=builder.as_markup()
            )
            return
        
        # Store selected date in state
        await state.update_data(selected_date=selected_date)
        
        builder = InlineKeyboardBuilder()
        builder.button(
            text="❌ Cancel",
            callback_data=TaskActionCD(action="view", task_id=data['task_id']).pack()
        )
        builder.adjust(1)
        await call.message.edit_text(
            f"Selected date: {selected_date}\n"
            f"Please enter time in format HH:MM (e.g. 09:30):",
            reply_markup=builder.as_markup()
        )

@router.message(FSMTaskEdit.edit_value)
async def process_edit_value(message: Message, state: FSMContext, conn):
    data = await state.get_data()
    field = data['field']
    task_id = data['task_id']
    
    task = await Task.get_by_id(conn, task_id)
    if not task:
        await message.answer("Task not found!")
        await state.clear()
        return

    if field in ['start_ts', 'end_ts']:
        try:
            selected_date = data.get('selected_date')
            if not selected_date:
                # If no date was selected, the user is trying to enter full datetime
                new_datetime = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
                new_value = message.text
            else:
                # If date was selected, user is entering only time
                time = datetime.strptime(message.text, "%H:%M").strftime("%H:%M")
                new_value = f"{selected_date} {time}"
                new_datetime = datetime.strptime(new_value, "%Y-%m-%d %H:%M")

            current_start = datetime.strptime(data['current_start'], "%Y-%m-%d %H:%M")
            current_end = datetime.strptime(data['current_end'], "%Y-%m-%d %H:%M")
            
            if field == 'start_ts' and new_datetime >= current_end:
                builder = InlineKeyboardBuilder()
                builder.button(
                    text="📅 Change End Time Instead",
                    callback_data=TaskEditCD(field="end_ts", task_id=task_id).pack()
                )
                builder.button(
                    text="🔄 Select Different Start Time",
                    callback_data=TaskEditCD(field="start_ts", task_id=task_id).pack()
                )
                builder.button(
                    text="❌ Cancel",
                    callback_data=TaskActionCD(action="view", task_id=task_id).pack()
                )
                builder.adjust(1)
                await message.answer(
                    f"Error: Start time cannot be after end time ({current_end.strftime('%Y-%m-%d %H:%M')}).\n"
                    f"Please choose:",
                    reply_markup=builder.as_markup()
                )
                return
            
            elif field == 'end_ts' and new_datetime <= current_start:
                builder = InlineKeyboardBuilder()
                builder.button(
                    text="📅 Change Start Time Instead",
                    callback_data=TaskEditCD(field="start_ts", task_id=task_id).pack()
                )
                builder.button(
                    text="🔄 Select Different End Time",
                    callback_data=TaskEditCD(field="end_ts", task_id=task_id).pack()
                )
                builder.button(
                    text="❌ Cancel",
                    callback_data=TaskActionCD(action="view", task_id=task_id).pack()
                )
                builder.adjust(1)
                await message.answer(
                    f"Error: End time cannot be before start time ({current_start.strftime('%Y-%m-%d %H:%M')}).\n"
                    f"Please choose:",
                    reply_markup=builder.as_markup()
                )
                return
                
        except ValueError:
            builder = InlineKeyboardBuilder()
            builder.button(
                text="📅 Select from Calendar",
                callback_data=TaskEditCD(field=field, task_id=task_id).pack()
            )
            builder.button(
                text="❌ Cancel",
                callback_data=TaskActionCD(action="view", task_id=task_id).pack()
            )
            builder.adjust(1)
            await message.answer(
                "Invalid time format. Please use HH:MM format (e.g. 09:30) or select from calendar:",
                reply_markup=builder.as_markup()
            )
            return

    # Confirm the change
    text = f"Confirm changing {field} to:\n\n{new_value}\n\nDo you want to proceed?"
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Confirm",
        callback_data=TaskEditConfirmCD(action="confirm", task_id=task_id, field=field).pack()
    )
    builder.button(
        text="❌ Cancel",
        callback_data=TaskEditConfirmCD(action="cancel", task_id=task_id, field=field).pack()
    )
    builder.button(
        text="🔄 Enter Different Value",
        callback_data=TaskEditCD(field=field, task_id=task_id).pack()
    )
    
    builder.adjust(2, 1)
    await state.update_data(new_value=new_value)
    await state.set_state(FSMTaskEdit.confirm_edit)
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(TaskEditConfirmCD.filter())
async def process_edit_confirmation(call: CallbackQuery, callback_data: TaskEditConfirmCD, state: FSMContext, conn):
    if callback_data.action == "cancel":
        await state.clear()
        await call.message.edit_text("Edit cancelled")
        await show_task_details(call, TaskActionCD(action="view", task_id=callback_data.task_id), conn)
        return

    data = await state.get_data()
    new_value = data['new_value']
    field = callback_data.field
    task_id = callback_data.task_id

    # Update the task
    updated_task = await Task.update(conn, task_id, **{field: new_value})
    if updated_task:
        await call.message.edit_text(f"{field} updated successfully!")
        logger.info(f"User {call.from_user.username} (id={call.from_user.id}) updated task {task_id} {field}")
        # Return to task view
        await show_task_details(call, TaskActionCD(action="view", task_id=task_id), conn)
    else:
        await call.message.edit_text("Failed to update task")
        logger.error(f"User {call.from_user.username} (id={call.from_user.id}) failed to update task {task_id} {field}")

    await state.clear()