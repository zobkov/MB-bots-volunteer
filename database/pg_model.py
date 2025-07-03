import asyncpg
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from utils.event_time import EventTime, EventTimeManager
import logging

async def create_pool(**kwargs) -> asyncpg.Pool:
    """Create a connection pool for PostgreSQL"""
    return await asyncpg.create_pool(**kwargs)

@dataclass
class User:
    tg_id: int
    tg_username: str
    name: str
    role: str

    @staticmethod
    async def create(pool: asyncpg.Pool, tg_id: int, tg_username: str, name: str, role: str) -> 'User':
        async with pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO users (tg_id, tg_username, name, role) 
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (tg_id) DO UPDATE 
                SET tg_username = $2, name = $3, role = $4
                ''',
                tg_id, tg_username, name, role
            )
        return User(tg_id=tg_id, tg_username=tg_username, name=name, role=role)

    @staticmethod
    async def get_by_tg_id(pool: asyncpg.Pool, tg_id: int) -> Optional['User']:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM users WHERE tg_id = $1', tg_id)
            if row:
                return User(tg_id=row['tg_id'], 
                          tg_username=row['tg_username'], 
                          name=row['name'], 
                          role=row['role'])
        return None

    @staticmethod
    async def get_all(pool: asyncpg.Pool) -> List['User']:
        async with pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM users')
            return [User(tg_id=row['tg_id'],
                        tg_username=row['tg_username'],
                        name=row['name'],
                        role=row['role']) for row in rows]

    @staticmethod
    async def update_role(pool: asyncpg.Pool, tg_id: int, new_role: str) -> Optional['User']:
        async with pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET role = $1 WHERE tg_id = $2',
                new_role, tg_id
            )
        return await User.get_by_tg_id(pool, tg_id)

    @staticmethod
    async def get_by_role(pool: asyncpg.Pool, role: str) -> List['User']:
        """Get all users with specified role"""
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                '''
                SELECT * FROM users WHERE role = $1
                ''',
                role
            )
            return [User(**dict(row)) for row in rows]

    @staticmethod
    async def get_by_role_and_status(pool, role: str, status: str) -> List['User']:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM users 
                WHERE role = $1 AND status = $2
                ORDER BY name
                """,
                role, status
            )
            return [User(**dict(row)) for row in rows]

@dataclass
class Task:
    task_id: Optional[int]
    title: str
    description: str
    start_day: int
    start_time: str
    end_day: int
    end_time: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @staticmethod
    async def create(pool: asyncpg.Pool, title: str, description: str, 
                    start_event_time: EventTime, end_event_time: EventTime, 
                    status: str) -> 'Task':
        created_at = datetime.now()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                '''
                INSERT INTO task (
                    title, description, 
                    start_day, start_time, 
                    end_day, end_time,
                    status, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
                ''',
                title, description,
                start_event_time.day, start_event_time.time,
                end_event_time.day, end_event_time.time,
                status, created_at
            )
            
            return Task(
                task_id=row['task_id'],
                title=row['title'],
                description=row['description'],
                start_day=row['start_day'],
                start_time=row['start_time'],
                end_day=row['end_day'],
                end_time=row['end_time'],
                status=row['status'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at']
            )

    def get_absolute_times(self, event_manager: EventTimeManager) -> tuple[datetime, datetime]:
        """Возвращает абсолютные даты начала и конца задания"""
        start = event_manager.to_absolute_time(EventTime(self.start_day, self.start_time))
        end = event_manager.to_absolute_time(EventTime(self.end_day, self.end_time))
        return start, end

    @staticmethod
    async def get_all(pool: asyncpg.Pool) -> List['Task']:
        async with pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM task')
            return [
                Task(
                    task_id=row['task_id'],
                    title=row['title'],
                    description=row['description'],
                    start_day=row['start_day'],
                    start_time=row['start_time'],
                    end_day=row['end_day'],
                    end_time=row['end_time'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    completed_at=row['completed_at']
                ) for row in rows
            ]
    
    @staticmethod
    async def get_by_id(pool: asyncpg.Pool, task_id: int) -> Optional['Task']:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM task WHERE task_id = $1', task_id)
            if row:
                return Task(
                    task_id=row['task_id'],
                    title=row['title'],
                    description=row['description'],
                    start_day=row['start_day'],
                    start_time=row['start_time'],
                    end_day=row['end_day'],
                    end_time=row['end_time'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    completed_at=row['completed_at']
                )
        return None

    @staticmethod
    async def update(pool: asyncpg.Pool, task_id: int, **kwargs) -> Optional['Task']:
        """Update task fields and return updated task"""
        async with pool.acquire() as conn:
            # Build update query dynamically
            update_fields = []
            values = []
            for idx, (field, value) in enumerate(kwargs.items(), start=1):
                if field in ['start_ts', 'end_ts'] and isinstance(value, str):
                    try:
                        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        value = datetime.strptime(value, "%Y-%m-%d %H:%M")
                update_fields.append(f"{field} = ${idx}")
                values.append(value)
            
            if not update_fields:
                return None
                
            # Add updated_at timestamp
            values.append(datetime.now())
            values.append(task_id)
            
            query = f"""
                UPDATE task 
                SET {', '.join(update_fields)}, updated_at = ${len(values)-1}
                WHERE task_id = ${len(values)}
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *values)
            
            if row:
                return Task(
                    task_id=row['task_id'],
                    title=row['title'],
                    description=row['description'],
                    start_day=row['start_day'],
                    start_time=row['start_time'],
                    end_day=row['end_day'],
                    end_time=row['end_time'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    completed_at=row['completed_at']
                )
            return None

    @staticmethod
    async def delete(pool, task_id: int) -> bool:
        logger = logging.getLogger(__name__)
        from database.pg_model import Assignment  # Avoid circular import
        async with pool.acquire() as conn:
            try:
                # First, delete all assignments for this task
                await Assignment.delete_by_task(pool, task_id)
                # Then, delete the task itself
                result = await conn.execute("DELETE FROM task WHERE task_id = $1", task_id)
                if result == "DELETE 1":
                    logger.info(f"Task {task_id} deleted successfully.")
                    return True
                else:
                    logger.warning(f"Task {task_id} not found or not deleted.")
                    return False
            except Exception as e:
                logger.error(f"Error deleting task {task_id}: {e}")
                return False

@dataclass
class Assignment:
    assign_id: Optional[int]
    task_id: int 
    tg_id: int
    assigned_by: int
    assigned_at: datetime
    start_day: int
    start_time: str
    end_day: int
    end_time: str
    status: str
    notification_scheduled: bool = False  # Флаг для отслеживания запланированных уведомлений

    @staticmethod
    async def create(pool: asyncpg.Pool, task_id: int, tg_id: int, assigned_by: int,
                    start_day: int, start_time: str, end_day: int, end_time: str,
                    status: str = 'assigned') -> 'Assignment':
        """Create a new assignment"""
        assigned_at = datetime.now()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                '''
                INSERT INTO assignment (
                    task_id, tg_id, assigned_by, assigned_at,
                    start_day, start_time, end_day, end_time, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                ''',
                task_id, tg_id, assigned_by, assigned_at,
                start_day, start_time, end_day, end_time, status
            )
            
            return Assignment(
                assign_id=row['assign_id'],
                task_id=row['task_id'],
                tg_id=row['tg_id'],
                assigned_by=row['assigned_by'],
                assigned_at=row['assigned_at'],
                start_day=row['start_day'],
                start_time=row['start_time'],
                end_day=row['end_day'],
                end_time=row['end_time'],
                status=row['status']
            )

    @staticmethod
    async def get_by_task(pool: asyncpg.Pool, task_id: int) -> List['Assignment']:
        """Get all assignments for a specific task"""
        async with pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM assignment WHERE task_id = $1', task_id)
            return [
                Assignment(
                    assign_id=row['assign_id'],
                    task_id=row['task_id'],
                    tg_id=row['tg_id'],
                    assigned_by=row['assigned_by'],
                    assigned_at=row['assigned_at'],
                    start_day=row['start_day'],
                    start_time=row['start_time'],
                    end_day=row['end_day'],
                    end_time=row['end_time'],
                    status=row['status']
                ) for row in rows
            ]

    @staticmethod
    async def get_by_volunteer(pool: asyncpg.Pool, tg_id: int) -> List['Assignment']:
        """Get all assignments for a specific volunteer"""
        async with pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM assignment WHERE tg_id = $1', tg_id)
            return [
                Assignment(
                    assign_id=row['assign_id'],
                    task_id=row['task_id'],
                    tg_id=row['tg_id'],
                    assigned_by=row['assigned_by'],
                    assigned_at=row['assigned_at'],
                    start_day=row['start_day'],
                    start_time=row['start_time'],
                    end_day=row['end_day'],
                    end_time=row['end_time'],
                    status=row['status']
                ) for row in rows
            ]

    @staticmethod
    async def update_status(pool: asyncpg.Pool, assign_id: int, new_status: str) -> Optional['Assignment']:
        """Update assignment status"""
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                '''
                UPDATE assignment 
                SET status = $1
                WHERE assign_id = $2
                RETURNING *
                ''',
                new_status, assign_id
            )
            
            if row:
                return Assignment(
                    assign_id=row['assign_id'],
                    task_id=row['task_id'],
                    tg_id=row['tg_id'],
                    assigned_by=row['assigned_by'],
                    assigned_at=row['assigned_at'],
                    start_day=row['start_day'],
                    start_time=row['start_time'],
                    end_day=row['end_day'],
                    end_time=row['end_time'],
                    status=row['status']
                )
        return None

    def get_absolute_times(self, event_manager: EventTimeManager) -> tuple[datetime, datetime]:
        """Get absolute start and end times for the assignment"""
        start = event_manager.to_absolute_time(EventTime(self.start_day, self.start_time))
        end = event_manager.to_absolute_time(EventTime(self.end_day, self.end_time))
        return start, end

    @staticmethod
    async def get_all_with_details(pool: asyncpg.Pool) -> List['Assignment']:
        """Get all assignments with task and volunteer details"""
        async with pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT a.*, t.title as task_title, 
                       u.name as volunteer_name, u.tg_username as volunteer_username
                FROM assignment a
                JOIN task t ON a.task_id = t.task_id
                JOIN users u ON a.tg_id = u.tg_id
                ORDER BY t.task_id, a.assigned_at
            ''')
            
            return [Assignment(
                assign_id=row['assign_id'],
                task_id=row['task_id'],
                tg_id=row['tg_id'],
                assigned_by=row['assigned_by'],
                assigned_at=row['assigned_at'],
                start_day=row['start_day'],
                start_time=row['start_time'],
                end_day=row['end_day'],
                end_time=row['end_time'],
                status=row['status']
            ) for row in rows]

    @staticmethod
    async def mark_notification_scheduled(pool: asyncpg.Pool, assign_id: int) -> None:
        """Mark assignment as having scheduled notification"""
        async with pool.acquire() as conn:
            await conn.execute(
                '''
                UPDATE assignment 
                SET notification_scheduled = true
                WHERE assign_id = $1
                ''',
                assign_id
            )

    @staticmethod
    async def get_pending_notifications(pool: asyncpg.Pool) -> List['Assignment']:
        """Get all assignments that need notifications"""
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                '''
                SELECT * FROM assignment 
                WHERE notification_scheduled = false 
                AND status = 'assigned'
                '''
            )
            return [Assignment(**dict(row)) for row in rows]

    @staticmethod
    async def get_by_id(pool: asyncpg.Pool, assign_id: int) -> Optional['Assignment']:
        """Get assignment by its ID"""
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                '''
                SELECT * FROM assignment 
                WHERE assign_id = $1
                ''',
                assign_id
            )
            return Assignment(**dict(row)) if row else None

    @staticmethod
    async def update(pool: asyncpg.Pool, assign_id: int, **kwargs) -> Optional['Assignment']:
        """Update assignment fields"""
        if not kwargs:
            return None
            
        set_fields = []
        values = []
        for i, (key, value) in enumerate(kwargs.items(), start=1):
            set_fields.append(f"{key} = ${i}")
            values.append(value)
        values.append(assign_id)
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f'''
                UPDATE assignment 
                SET {", ".join(set_fields)}
                WHERE assign_id = ${len(values)}
                RETURNING *
                ''',
                *values
            )
            
            if row:
                return Assignment(**dict(row))
        return None

    @staticmethod
    async def delete_by_task(pool, task_id: int) -> int:
        logger = logging.getLogger(__name__)
        async with pool.acquire() as conn:
            try:
                result = await conn.execute("DELETE FROM assignment WHERE task_id = $1", task_id)
                deleted_count = int(result.split()[-1]) if "DELETE" in result else 0
                logger.info(f"Deleted {deleted_count} assignments for task {task_id}")
                return deleted_count
            except Exception as e:
                logger.error(f"Error deleting assignments for task {task_id}: {e}")
                return 0

@dataclass
class PendingUser:
    tg_username: str
    name: str
    role: str

    @staticmethod
    async def create(pool: asyncpg.Pool, tg_username: str, name: str, role: str) -> 'PendingUser':
        async with pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO pending_users (tg_username, name, role) 
                VALUES ($1, $2, $3)
                ON CONFLICT (tg_username) DO UPDATE 
                SET name = $2, role = $3
                ''',
                tg_username, name, role
            )
        return PendingUser(tg_username=tg_username, name=name, role=role)

    @staticmethod
    async def get_by_username(pool: asyncpg.Pool, tg_username: str) -> Optional['PendingUser']:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM pending_users WHERE tg_username = $1',
                tg_username
            )
            if row:
                return PendingUser(
                    tg_username=row['tg_username'],
                    name=row['name'],
                    role=row['role']
                )
        return None

    @staticmethod
    async def delete(pool: asyncpg.Pool, tg_username: str) -> bool:
        async with pool.acquire() as conn:
            result = await conn.execute(
                'DELETE FROM pending_users WHERE tg_username = $1',
                tg_username
            )
            return 'DELETE 1' in result

    @staticmethod
    async def get_all(pool: asyncpg.Pool) -> List['PendingUser']:
        """Get all pending users."""
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                '''
                SELECT * FROM pending_users
                WHERE role = 'volunteer'
                ORDER BY name
                '''
            )
            return [PendingUser(**dict(row)) for row in rows]