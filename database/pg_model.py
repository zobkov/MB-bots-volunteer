from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import asyncpg

from utils.date_format import datetime_format_str

# Utility functions
async def create_pool(dsn: str = None, **kwargs) -> asyncpg.Pool:
    """Create and return a connection pool to the PostgreSQL database."""
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
    start_ts: datetime
    end_ts: datetime
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @staticmethod
    async def create(pool: asyncpg.Pool, title: str, description: str, 
                    start_ts: str, end_ts: str, status: str) -> 'Task':
        created_at = datetime.now()
        # Convert string dates to datetime objects
        start_datetime = datetime.strptime(start_ts, "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(end_ts, "%Y-%m-%d %H:%M")
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                '''
                INSERT INTO task (title, description, start_ts, end_ts, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                ''',
                title, description, start_datetime, end_datetime, status, created_at
            )
            
            return Task(
                task_id=row['task_id'],
                title=row['title'],
                description=row['description'],
                start_ts=row['start_ts'],
                end_ts=row['end_ts'],
                status=row['status'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at']
            )

    @staticmethod
    async def get_all(pool: asyncpg.Pool) -> List['Task']:
        async with pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM task')
            return [
                Task(
                    task_id=row['task_id'],
                    title=row['title'],
                    description=row['description'],
                    start_ts=row['start_ts'],
                    end_ts=row['end_ts'],
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
                    start_ts=row['start_ts'],
                    end_ts=row['end_ts'],
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
                    start_ts=row['start_ts'],
                    end_ts=row['end_ts'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    completed_at=row['completed_at']
                )
            return None