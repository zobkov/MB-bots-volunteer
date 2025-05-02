from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import aiosqlite

from utils.date_format import datetime_format_str

# Utility functions
async def create_connection(path: str = 'sqlite.db') -> aiosqlite.Connection:
    """Create and return a connection to the SQLite database."""
    return await aiosqlite.connect(path)

async def close_connection(conn: aiosqlite.Connection):
    conn.close()

async def get_by_filter(conn: aiosqlite.Connection, table_name: str, column_name: str, value) -> List[tuple]:
    """Get rows from a table based on a specific filter."""
    query = f"SELECT * FROM {table_name} WHERE {column_name} = ?"
    async with conn.execute(query, (value,)) as cursor:
        return await cursor.fetchall()

@dataclass
class User:
    tg_id: int
    tg_username: str
    name: str
    role: str

    @staticmethod
    async def create(conn: aiosqlite.Connection, tg_id: int, tg_username: str, name: str, role: str) -> 'User':
        await conn.execute(
            'INSERT OR REPLACE INTO users (tg_id, tg_username, name, role) VALUES (?, ?, ?, ?)',
            (tg_id, tg_username, name, role)
        )
        await conn.commit()
        return User(tg_id=tg_id, tg_username=tg_username, name=name, role=role)

    @staticmethod
    async def get_by_tg_id(conn: aiosqlite.Connection, tg_id: int) -> Optional['User']:
        async with conn.execute('SELECT * FROM users WHERE tg_id = ?', (tg_id,)) as cursor:
            if row := await cursor.fetchone():
                return User(tg_id=row[0], tg_username=row[1], name=row[2], role=row[3])
        return None

    @staticmethod
    async def get_all(conn: aiosqlite.Connection) -> List['User']:
        async with conn.execute('SELECT * FROM users') as cursor:
            rows = await cursor.fetchall()
            return [User(tg_id=row[0], tg_username=row[1], name=row[2], role=row[3]) for row in rows]

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
    async def create(conn: aiosqlite.Connection, title: str, description: str, 
                    start_ts: str, end_ts: str, status: str) -> 'Task':
        created_at = datetime.now()
        await conn.execute(
            '''
            INSERT INTO task (title, description, start_ts, end_ts, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (title, description, datetime_format_str(start_ts), datetime_format_str(end_ts), status, datetime_format_str(datetime.now()))
        )
        await conn.commit()
        
        # Get the last inserted task
        async with conn.execute('SELECT last_insert_rowid()') as cursor:
            task_id = (await cursor.fetchone())[0]
            
        return Task(
            task_id=task_id,
            title=title,
            description=description,
            start_ts=datetime.strptime(start_ts, "%Y-%m-%d %H:%M"),
            end_ts=datetime.strptime(end_ts, "%Y-%m-%d %H:%M"),
            status=status,
            created_at=created_at
        )

    @staticmethod
    async def get_all(conn: aiosqlite.Connection) -> List['Task']:
        async with conn.execute('SELECT * FROM task') as cursor:
            rows = await cursor.fetchall()
            return [
                Task(
                    task_id=row[0],
                    title=row[1],
                    description=row[2],
                    start_ts=datetime.fromisoformat(row[3]),
                    end_ts=datetime.fromisoformat(row[4]),
                    status=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    updated_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    completed_at=datetime.fromisoformat(row[8]) if row[8] else None
                ) for row in rows
            ]

@dataclass
class Assignment:
    assign_id: Optional[int]
    task_id: int
    tg_id: int
    assigned_by: int
    assigned_at: datetime
    start_ts: datetime
    end_ts: datetime
    status: str

    @staticmethod
    async def create(conn: aiosqlite.Connection, task_id: int, tg_id: int, 
                    assigned_by: int, start_ts: str, end_ts: str,
                    status: str = 'unscheduled') -> 'Assignment':
        assigned_at = datetime_format_str(datetime.now())
        await conn.execute(
            '''
            INSERT INTO assignment (task_id, tg_id, assigned_by, assigned_at, start_ts, end_ts, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (task_id, tg_id, assigned_by, assigned_at, 
             datetime_format_str(start_ts), datetime_format_str(end_ts), status)
        )
        await conn.commit()

        async with conn.execute('SELECT last_insert_rowid()') as cursor:
            assign_id = (await cursor.fetchone())[0]

        return Assignment(
            assign_id=assign_id,
            task_id=task_id,
            tg_id=tg_id,
            assigned_by=assigned_by,
            assigned_at=assigned_at,
            start_ts=datetime.strptime(start_ts, "%Y-%m-%d %H:%M"),
            end_ts=datetime.strptime(end_ts, "%Y-%m-%d %H:%M"),
            status=status
        )

    @staticmethod
    async def get_all(conn: aiosqlite.Connection) -> List['Assignment']:
        async with conn.execute('SELECT * FROM assignment') as cursor:
            rows = await cursor.fetchall()
            return [
                Assignment(
                    assign_id=row[0],
                    task_id=row[1],
                    tg_id=row[2],
                    assigned_by=row[3],
                    assigned_at=datetime.fromisoformat(row[4]),
                    start_ts=datetime.fromisoformat(row[5]),
                    end_ts=datetime.fromisoformat(row[6]),
                    status=row[7]
                ) for row in rows
            ]

    @staticmethod
    async def get_by_tg_id(conn: aiosqlite.Connection, tg_id: int) -> List['Assignment']:
        async with conn.execute('SELECT * FROM assignment WHERE tg_id = ?', (tg_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                Assignment(
                    assign_id=row[0],
                    task_id=row[1],
                    tg_id=row[2],
                    assigned_by=row[3],
                    assigned_at=datetime.fromisoformat(row[4]),
                    start_ts=datetime.fromisoformat(row[5]),
                    end_ts=datetime.fromisoformat(row[6]),
                    status=row[7]
                ) for row in rows
            ]

@dataclass
class AuditLog:
    log_id: Optional[int]
    table_name: str
    operation: str
    record_id: Optional[int]
    timestamp: datetime
    details: str

    @staticmethod
    async def log(conn: aiosqlite.Connection, table_name: str, operation: str, 
                 record_id: Optional[int], details: str) -> 'AuditLog':
        timestamp = datetime.now()
        await conn.execute(
            '''
            INSERT INTO audit_log (table_name, operation, record_id, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (table_name, operation, record_id, timestamp.isoformat(), details)
        )
        await conn.commit()

        async with conn.execute('SELECT last_insert_rowid()') as cursor:
            log_id = (await cursor.fetchone())[0]

        return AuditLog(
            log_id=log_id,
            table_name=table_name,
            operation=operation,
            record_id=record_id,
            timestamp=timestamp,
            details=details
        )
