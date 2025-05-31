import logging
from database.pg_model import Assignment, Task, User
from aiogram import Bot

from services.assignment_service import AssignmentService

logger = logging.getLogger(__name__)

async def notify_task_volunteers(task_id: int, bot_token: str, db_config: dict):
    """Notification function that can be serialized by APScheduler"""
    try:
        import asyncpg
        
        # Create new bot instance
        bot = Bot(token=bot_token)
        
        # Create new pool connection
        pool = await asyncpg.create_pool(**db_config)
        
        # Get task and assignments
        async with pool.acquire() as conn:
            task = await Task.get_by_id(pool, task_id)
            assignments = await Assignment.get_by_task(pool, task_id)
            
            for assignment in assignments:
                volunteer = await User.get_by_tg_id(pool, assignment.tg_id)
                message = (
                    f"🔔 Напоминание о задании через 5 минут!\n\n"
                    f"📋 {task.title}\n"
                    f"📝 {task.description}\n"
                    f"🕒 Начало: День {assignment.start_day} {assignment.start_time}\n"
                    f"🕕 Конец: День {assignment.end_day} {assignment.end_time}"
                )
                
                try:
                    await bot.send_message(volunteer.tg_id, message)
                except Exception as e:
                    logger.error(f"Failed to send notification to user {volunteer.tg_id}: {e}")
                    
        await bot.session.close()
        await pool.close()
        
    except Exception as e:
        logger.error(f"Error in notification task: {e}")