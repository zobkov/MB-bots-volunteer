from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime, timedelta
from utils.event_time import EventTime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.pg_model import Task, User, Assignment
from services.assignment_service import AssignmentService
from utils.event_time import EventTimeManager

router = Router()

@router.message(Command("debug_status"))
async def debug_status(message: Message, event_manager: EventTimeManager):
    """Показывает текущий статус времени"""
    current_time = event_manager.current_time
    current_day = event_manager.get_current_event_day()
    status = event_manager.get_current_status()
    
    await message.answer(
        f"Текущий статус:\n"
        f"{status}\n\n"
        f"Абсолютное время: {current_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"Debug mode: {'включен' if event_manager.debug_mode else 'выключен'}"
    )

@router.message(Command("set_debug_time"))
async def set_debug_time(message: Message, event_manager: EventTimeManager):
    """Устанавливает отладочное время. Формат: /set_debug_time <день> <ЧЧ:ММ>"""
    if not event_manager.debug_mode:
        await message.answer(
            "Debug mode не включен!\n"
            "Добавьте DEBUG_MODE=true в .env файл"
        )
        return

    try:
        # Format: /set_debug_time 2 14:30 (день 2, 14:30)
        _, day, time = message.text.split()
        day = int(day)
        
        # Проверяем формат времени
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            raise ValueError("Неверный формат времени")
            
        # Конвертируем в абсолютное время
        debug_time = event_manager.datetime_from_event_day(day, time)
        event_manager.set_debug_time(debug_time)
        
        # Получаем текущий статус
        status = event_manager.get_current_status()
        
        await message.answer(
            f"Отладочное время установлено!\n\n"
            f"Статус: {status}\n"
            f"Абсолютное время: {debug_time.strftime('%Y-%m-%d %H:%M')}"
        )
        
    except ValueError as e:
        await message.answer(
            f"Ошибка: {str(e)}\n\n"
            f"Формат: /set_debug_time <день> <ЧЧ:ММ>\n"
            f"Пример: /set_debug_time 2 14:30\n"
            f"День должен быть от 1 до {event_manager.days_count}"
        )
    except IndexError:
        await message.answer(
            "Неверный формат команды!\n\n"
            "Формат: /set_debug_time <день> <ЧЧ:ММ>\n"
            "Пример: /set_debug_time 2 14:30"
        )

@router.message(Command("debug_assign"))
async def debug_assign_handler(message: Message, command: Command, pool=None, scheduler: AsyncIOScheduler = None, event_manager: EventTimeManager = None):
    """Debug command to assign volunteer to task. Usage: /debug_assign volunteer_id task_id"""
    if not pool:
        return await message.reply("❌ No database connection")
    
    if not scheduler:
        return await message.reply("❌ No scheduler available")
        
    if not event_manager:
        return await message.reply("❌ No event manager available")
        
    if not command.args:
        return await message.reply("Usage: /debug_assign volunteer_id task_id")
    
    try:
        vol_id, task_id = map(int, command.args.split())
        
        # Check if task exists
        task = await Task.get_by_id(pool, task_id)
        if not task:
            return await message.reply(f"❌ Task {task_id} not found")
            
        # Check if volunteer exists
        volunteer = await User.get_by_tg_id(pool, vol_id)
        if not volunteer:
            return await message.reply(f"❌ Volunteer {vol_id} not found")
        
        # Check for existing assignment for the same volunteer
        existing_assignments = await Assignment.get_by_volunteer(pool, vol_id)
        for assignment in existing_assignments:
            if assignment.task_id == task_id and assignment.status != 'cancelled':
                # Cancel the existing assignment
                await Assignment.update_status(pool, assignment.assign_id, 'cancelled')
                
                # Remove the associated notification
                job_id = f'notification_task_{assignment.task_id}_assignment_{assignment.assign_id}'
                try:
                    scheduler.remove_job(job_id)
                except Exception:
                    pass
                
                await message.reply(f"❌ Existing assignment for volunteer {vol_id} on task {task_id} has been cancelled.")
        
        # Create new assignment
        service = AssignmentService(message.bot, pool)
        assignments = await service.create_assignment(
            task_id=task_id,
            volunteer_ids=[vol_id],
            admin_id=message.from_user.id
        )
        
        if assignments:
            assignment = assignments[0]
            
            # Calculate notification time
            start_time = event_manager.to_absolute_time(
                EventTime(day=task.start_day, time=task.start_time)
            )
            notification_time = start_time - timedelta(minutes=5)

            # Get database config
            db_config = {
                'user': pool._connect_kwargs['user'],
                'password': pool._connect_kwargs['password'],
                'database': pool._connect_kwargs['database'],
                'host': pool._connect_kwargs['host'],
                'port': pool._connect_kwargs['port']
            }
            
            # Schedule notification
            job_id = f'notification_task_{task_id}_assignment_{assignment.assign_id}'
            scheduler.add_job(
                'services.notifications:notify_task_volunteers',
                'date',
                run_date=notification_time,
                args=[task_id, message.bot.token, db_config, event_manager.debug_mode, assignment.assign_id],
                id=job_id,
                replace_existing=True
            )
            await Assignment.mark_notification_scheduled(pool, assignment.assign_id)
            
            # Create success message with assignment and notification details
            text = (
                f"✅ Assignment created:\n"
                f"Task: {task.title} (ID: {task_id})\n"
                f"Volunteer: {volunteer.name} (@{volunteer.tg_username}, ID: {vol_id})\n"
                f"Time: День {assignment.start_day} {assignment.start_time} - "
                f"День {assignment.end_day} {assignment.end_time}\n"
                f"📅 Notification scheduled for: {notification_time.strftime('%Y-%m-%d %H:%M')}"
            )
            await message.reply(text)
        else:
            await message.reply("❌ Failed to create assignment")
            
    except ValueError:
        await message.reply("❌ Invalid format. Usage: /debug_assign volunteer_id task_id")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")