import logging
from database.pg_model import Assignment, Task, User
from aiogram import Bot

from services.assignment_service import AssignmentService

logger = logging.getLogger(__name__)

async def notify_task_volunteers(task_id: int, bot_token: str, db_config: dict, debug_mode: bool = False, assign_id: int = None):
    """Notification function that can be serialized by APScheduler"""
    try:
        import asyncpg
        
        bot = Bot(token=bot_token)
        pool = await asyncpg.create_pool(**db_config)
        
        async with pool.acquire() as conn:
            task = await Task.get_by_id(pool, task_id)
            
            # Get either specific assignment or all active assignments
            if assign_id:
                assignments = [await Assignment.get_by_id(pool, assign_id)]
            else:
                assignments = await Assignment.get_by_task(pool, task_id)
                assignments = [a for a in assignments if a.status != 'cancelled']
            
            failed_notifications = []
            
            for assignment in assignments:
                if assignment:  # Check if assignment exists
                    volunteer = await User.get_by_tg_id(pool, assignment.tg_id)
                    message = (
                        f"🔔 Напоминание о задании через 5 минут!\n\n"
                        f"📋 {task.title}\n"
                        f"📝 {task.description}\n"
                        f"🕒 Начало: День {assignment.start_day} {assignment.start_time}\n"
                        f"🕕 Конец: День {assignment.end_day} {assignment.end_time}"
                    )
                    
                    notification_status = "✅ успешно" 
                    try:
                        await bot.send_message(volunteer.tg_id, message)
                    except Exception as e:
                        notification_status = f"❌ ошибка: {str(e)}"
                        logger.error(f"Failed to send notification to user {volunteer.tg_id}: {e}")
                        failed_notifications.append((volunteer, str(e)))
                    
                    # Send debug info about this specific notification
                    if debug_mode:
                        try:
                            admins = await User.get_by_role(pool, "admin")
                            admin_message = (
                                f"<i>[DEBUG] Отправка уведомления</i>\n"
                                f"Задание: {task.title}\n"
                                f"Волонтер: {volunteer.name} (@{volunteer.tg_username})\n"
                                f"Статус: {notification_status}"
                            )
                            
                            for admin in admins:
                                await bot.send_message(admin.tg_id, admin_message)
                        except Exception as e:
                            logger.error(f"Failed to send debug notification: {e}")
                            
        await bot.session.close()
        await pool.close()
        
    except Exception as e:
        logger.error(f"Error in notification task: {e}")