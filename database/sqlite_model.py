import aiosqlite
from typing import List, Optional
import datetime

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

# Models
class User:
    @staticmethod
    async def create(conn: aiosqlite.Connection, tg_id: int, tg_username: str, name: str, role: str):
        """Insert or update a user with given role."""
        await conn.execute(
            '''
            INSERT OR REPLACE INTO users (tg_id, tg_username, name, role)
            VALUES (?, ?, ?, ?)
            ''',
            (tg_id, tg_username, name, role)
        )
        await conn.commit()

    @staticmethod
    async def get_by_tg_id(conn: aiosqlite.Connection, tg_id: int) -> Optional[tuple]:
        """Fetch a single user by their Telegram ID."""
        async with conn.execute(
            'SELECT * FROM users WHERE tg_id = ?',
            (tg_id,)
        ) as cursor:
            return await cursor.fetchone()

    @staticmethod
    async def get_all(conn: aiosqlite.Connection) -> List[tuple]:
        """Get all users."""
        async with conn.execute('SELECT * FROM users') as cursor:
            return await cursor.fetchall()

    @staticmethod
    async def update_role(conn: aiosqlite.Connection, tg_id: int, new_role: str):
        """Update the role of a user."""
        await conn.execute(
            'UPDATE users SET role = ? WHERE tg_id = ?',
            (new_role, tg_id)
        )
        await conn.commit()

    @staticmethod
    async def exists(conn: aiosqlite.Connection, tg_id: int) -> Optional[str]:
        """Return the role of a user by their Telegram ID, or None if not exists."""
        async with conn.execute(
            'SELECT role FROM users WHERE tg_id = ?',
            (tg_id,)
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else None

class Task:
    @staticmethod
    async def create(conn: aiosqlite.Connection, title: str, description: str, start_ts: str, end_ts: str, status: str):
        """Insert a new task."""
        await conn.execute(
            '''
            INSERT INTO task (title, description, start_ts, end_ts, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (title, description, start_ts, end_ts, status, datetime.datetime.now().isoformat())
        )
        await conn.commit()

    @staticmethod
    async def get_all(conn: aiosqlite.Connection) -> List[tuple]:
        """Get all tasks."""
        async with conn.execute('SELECT * FROM task') as cursor:
            return await cursor.fetchall()

    @staticmethod
    async def get_by_status(conn: aiosqlite.Connection, status: str) -> List[tuple]:
        """Get tasks filtered by status."""
        async with conn.execute(
            'SELECT * FROM task WHERE status = ?',
            (status,)
        ) as cursor:
            return await cursor.fetchall()

class Assignment:
    @staticmethod
    async def create(conn: aiosqlite.Connection, task_id: int, tg_id: int, assigned_by: int, assigned_at: str, status: str):
        """Assign a task to a user."""
        await conn.execute(
            '''
            INSERT INTO assignment (task_id, tg_id, assigned_by, assigned_at, status)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (task_id, tg_id, assigned_by, assigned_at, status)
        )
        await conn.commit()

    @staticmethod
    async def get_all(conn: aiosqlite.Connection) -> List[tuple]:
        """Get all assignments."""
        async with conn.execute('SELECT * FROM assignment') as cursor:
            return await cursor.fetchall()

    @staticmethod
    async def get_by_user(conn: aiosqlite.Connection, tg_id: int) -> List[tuple]:
        """Get all assignments for a specific user."""
        async with conn.execute(
            'SELECT * FROM assignment WHERE tg_id = ?',
            (tg_id,)
        ) as cursor:
            return await cursor.fetchall()

class AuditLog:
    @staticmethod
    async def log(conn: aiosqlite.Connection, table_name: str, operation: str, record_id: Optional[int], details: str):
        """Insert a record into the audit log."""
        await conn.execute(
            '''
            INSERT INTO audit_log (table_name, operation, record_id, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (table_name, operation, record_id, datetime.datetime.now().isoformat(), details)
        )
        await conn.commit()

    @staticmethod
    async def get_all(conn: aiosqlite.Connection) -> List[tuple]:
        """Get all audit log entries."""
        async with conn.execute('SELECT * FROM audit_log') as cursor:
            return await cursor.fetchall()
