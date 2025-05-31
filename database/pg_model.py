import asyncpg
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from utils.event_time import EventTime, EventTimeManager

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