import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from lexicon.lexicon_ru import LEXICON_RU 

from database.sqlite_model import User

from keyboards.admin import keyboard_main_menu, keyboard_assignment_list, keyboard_task_list

from filters.roles import IsAdmin

logger = logging.getLogger(__name__)

# Use this:
router = Router()
# Apply IsAdmin filter to all message handlers
router.message.filter(IsAdmin())
# Add filter for callback queries as well
router.callback_query.filter(IsAdmin())

# Then define your handlers
@router.message(CommandStart())
async def admin_handler(message: Message):
    await message.reply("Hello, fellow admin! Welcome to this bot")
    await message.answer(
        text = LEXICON_RU["main_menu"],
        reply_markup=keyboard_main_menu
        )

@router.message(Command(commands=['change_roles']))
async def admin_handler(message: Message, conn=None, middleware=None, **data):  # Changed from main_outer_middleware to middleware
    if conn and middleware:
        # Update role in database
        await User.update_role(conn, message.from_user.id, "volunteer")
        
        # Update cache in middleware
        middleware.role_cache[message.from_user.id] = "volunteer"
        
        # Update workflow data
        data["role"] = "volunteer"
        
        logger.info(f"User {message.from_user.username} (id={message.from_user.id}) has switched role to 'volunteer'")
        await message.answer("Role changed to volunteer")
    else:
        logger.error(f"User {message.from_user.username} (id={message.from_user.id}) tried to switch roles but missing connection or middleware")
        await message.answer("Configuration error")


@router.callback_query(F.data == 'admin-assignment_list')
async def process_assignment_list(callback: CallbackQuery):
    await callback.message.edit_text(
        text=LEXICON_RU['assignment_list'], 
        reply_markup=keyboard_assignment_list
    )
    # Add answer to prevent clock icon
    await callback.answer()

@router.callback_query(F.data == 'admin-tasks_list')
async def process_tasks_list(callback: CallbackQuery):
    await callback.message.edit_text(
        text=LEXICON_RU['tasks_list'], 
        reply_markup=keyboard_task_list
    )
    await callback.answer()

@router.callback_query(F.data == 'general-main_menu')
async def process_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        text=LEXICON_RU['main_menu'], 
        reply_markup=keyboard_main_menu
    )
    await callback.answer()

@router.callback_query(F.data == 'general-go_back')
async def process_go_back(callback: CallbackQuery):
    await callback.message.edit_text(
        text=LEXICON_RU['main_menu'], 
        reply_markup=keyboard_main_menu
    )
    await callback.answer()