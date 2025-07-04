import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon.lexicon_ru import LEXICON_RU, LEXICON_RU_BUTTONS
from filters.roles import IsVolunteer
from handlers.callbacks import NavigationCD
from keyboards.user import get_menu_markup
from keyboards.admin import get_menu_markup as get_admin_menu_markup
from database.pg_model import User, Assignment, Task, SpotTaskResponse
from utils.formatting import format_task_time

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
async def proccess_start(message: Message):
    await message.answer(
        text=LEXICON_RU["vmain"],
        reply_markup=get_menu_markup("vmain")
    )

@router.message(Command(commands=['change_roles']))
async def role_change_handler(message: Message, pool=None, middleware=None, **data):
    if not pool or not middleware:
        logger.error(f"User {message.from_user.username} (id={message.from_user.id}) tried to switch roles but missing pool or middleware")
        await message.answer("⚠️ Ошибка конфигурации. Попробуйте позже или обратитесь к администратору.")
        return
        
    try:
        await User.update_role(pool, message.from_user.id, "admin")
        middleware.role_cache[message.from_user.id] = "admin"
        data["role"] = "admin"
        
        logger.info(f"User {message.from_user.username} (id={message.from_user.id}) has switched role to 'admin'")
        await message.answer("✅ Роль изменена на администратора")
        await message.answer(
            text=LEXICON_RU['main'],
            reply_markup=get_admin_menu_markup("main")
        )
    except Exception as e:
        logger.error(f"Error changing role for user {message.from_user.id}: {e}")
        await message.answer("❌ Ошибка при смене роли")



@router.callback_query(NavigationCD.filter(F.path == "vmain.mytasks"))
async def show_volunteer_tasks(call: CallbackQuery, pool):
    # Get all active assignments for the volunteer
    assignments = await Assignment.get_by_volunteer(pool, call.from_user.id)
    active_assignments = [a for a in assignments if a.status != 'cancelled']
    
    logger.debug(f"Volunteer tasks: {active_assignments}")

    if not active_assignments:
        text = LEXICON_RU['vmain.mytasks.empty']
        builder = InlineKeyboardBuilder()
        builder.button(
            text=LEXICON_RU_BUTTONS['go_back'],
            callback_data=NavigationCD(path="vmain").pack()
        )
    else:
        tasks_text = []
        builder = InlineKeyboardBuilder()
        
        for assignment in active_assignments:
            task = await Task.get_by_id(pool, assignment.task_id)
            if task:
                # Add task info to text
                task_text = (
                    f"📌 <b>{task.title}</b>\n"
                    f"<i>{format_task_time(task)}</i>"
                )
                tasks_text.append(task_text)
                
                # Add button for task details
                builder.button(
                    text=f"📋 {task.title}",
                    callback_data=f"view_task_{task.task_id}"
                )
        
        # Add back button
        builder.button(
            text=LEXICON_RU_BUTTONS['go_back'],
            callback_data=NavigationCD(path="vmain").pack()
        )
        
        # Сначала формируем список заданий
        tasks_formatted = "\n\n".join(tasks_text)
        # Затем подставляем его в шаблон
        text = LEXICON_RU['vmain.mytasks'].format(tasks=tasks_formatted)
    
    # Adjust buttons layout - one button per row
    builder.adjust(1)
    
    await call.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"  # Добавляем parse_mode для HTML форматирования
    )

@router.callback_query(lambda c: c.data.startswith("view_task_"))
async def show_volunteer_task_details(call: CallbackQuery, pool):
    task_id = int(call.data.split("_")[2])
    task = await Task.get_by_id(pool, task_id)
    
    if not task:
        await call.answer("Задание не найдено!", show_alert=True)
        return
    
    # Format task details
    details = (
        f"<b>{task.title}</b>\n\n"
        f"📝 Описание: {task.description}\n"
        f"🕒 Время: {format_task_time(task)}\n"
    )
    
    text = LEXICON_RU['vmain.task_details'].format(details=details)
    
    # Create keyboard with back button
    builder = InlineKeyboardBuilder()
    builder.button(
        text=LEXICON_RU_BUTTONS['go_back_to_tasks'],
        callback_data=NavigationCD(path="vmain.mytasks").pack()
    )
    
    await call.message.edit_text(
        text,
        reply_markup=builder.as_markup()
    )

@router.callback_query(IsVolunteer(), F.data.startswith("spot_accept_") | F.data.startswith("spot_decline_"))
async def handle_spot_response(call: CallbackQuery, pool, bot):
    action, spot_task_id = call.data.split("_")[1:]
    volunteer_id = call.from_user.id
    response = "accepted" if action == "accept" else "declined"

    # Save response to DB
    await SpotTaskResponse.create(pool, int(spot_task_id), volunteer_id, response)
    await call.answer("Ответ отправлен!")

    # Notify all admins
    admins = await User.get_by_role(pool, "admin")
    volunteer = await User.get_by_tg_id(pool, volunteer_id)
    for admin in admins:
        await bot.send_message(
            admin.tg_id,
            f"Волонтер {volunteer.name} (@{volunteer.tg_username}) {'принял' if response == 'accepted' else 'отклонил'} срочное задание."
        )
    await bot.send_message(
        257026813,
        f"Волонтер {volunteer.name} (@{volunteer.tg_username}) {'принял' if response == 'accepted' else 'отклонил'} срочное задание."
        )

    # Optionally: schedule deletion of this message after expiry


@router.callback_query(NavigationCD.filter())
async def navigate_menu(call: CallbackQuery, callback_data: NavigationCD):
    new_path = callback_data.path
    await call.message.edit_text(
        text=LEXICON_RU[new_path],
        parse_mode="HTML",  # Изменяем Markdown на HTML
        reply_markup=get_menu_markup(new_path)
    )