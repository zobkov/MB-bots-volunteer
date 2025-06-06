
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from aiogram import Bot
from database.pg_model import User, Task, Assignment

logger = logging.getLogger(__name__)

class AssignmentService:
    def __init__(self, bot: Bot, pool):
        self.bot = bot
        self.pool = pool
        self.NOTIFICATION_MINUTES = 5  # За сколько минут уведомлять

    async def get_volunteers(self, page: int = 1, per_page: int = 5) -> tuple[List[User], int]:
        """Get paginated list of volunteers"""
        async with self.pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE role = 'volunteer'"
            )
            
            # Get paginated volunteers
            volunteers = await conn.fetch(
                """
                SELECT * FROM users 
                WHERE role = 'volunteer'
                ORDER BY name
                LIMIT $1 OFFSET $2
                """,
                per_page, (page - 1) * per_page
            )
            
            return [User(**dict(v)) for v in volunteers], total

    async def create_assignment(self, task_id: int, volunteer_ids: List[int], admin_id: int) -> List[Assignment]:
        """Create assignments for multiple volunteers"""
        assignments = []
        task = await Task.get_by_id(self.pool, task_id)
        if not task:
            raise ValueError("Task not found")

        for vol_id in volunteer_ids:
            assignment = await Assignment.create(
                pool=self.pool,
                task_id=task_id,
                tg_id=vol_id,
                assigned_by=admin_id,
                start_day=task.start_day,
                start_time=task.start_time,
                end_day=task.end_day,
                end_time=task.end_time,
                status='assigned'
            )
            assignments.append(assignment)

        return assignments

    async def notify_volunteers(self, task_id: int):
        """Send notifications to volunteers about upcoming task"""
        async with self.pool.acquire() as conn:
            # Get task and its assignments
            assignments = await conn.fetch(
                """
                SELECT a.*, u.tg_id, u.name, t.title, t.description
                FROM assignment a
                JOIN users u ON a.tg_id = u.tg_id
                JOIN task t ON a.task_id = t.task_id
                WHERE a.task_id = $1
                """,
                task_id
            )

            for assignment in assignments:
                message = (
                    f"🔔 Напоминание о задании!\n\n"
                    f"Через {self.NOTIFICATION_MINUTES} минут начинается:\n"
                    f"📋 {assignment['title']}\n"
                    f"📝 {assignment['description']}\n"
                    f"🕒 Начало: День {assignment['start_day']} {assignment['start_time']}\n"
                    f"🕕 Конец: День {assignment['end_day']} {assignment['end_time']}"
                )
                
                try:
                    await self.bot.send_message(assignment['tg_id'], message)
                except Exception as e:
                    logger.error(f"Failed to send notification to user {assignment['tg_id']}: {e}")