import asyncio
import aiosqlite

async def create_database(path: str = 'sqlite.db'):
    # Создаём БД и все таблицы
    async with aiosqlite.connect(path) as db:
        # Общая таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                tg_id        INTEGER PRIMARY KEY,
                tg_username  TEXT    UNIQUE NOT NULL,
                name         TEXT    NOT NULL,
                role         TEXT    NOT NULL    -- 'admin' или 'volunteer' и т.п.
            )
        ''')

        # Задания
        await db.execute('''
            CREATE TABLE IF NOT EXISTS task (
                task_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT    NOT NULL,
                description  TEXT,
                start_ts     TEXT    NOT NULL,
                end_ts       TEXT    NOT NULL,
                status       TEXT    NOT NULL,
                created_at   TEXT    NOT NULL,
                updated_at   TEXT,
                completed_at TEXT
            )
        ''')

        # Назначения
        await db.execute('''
            CREATE TABLE IF NOT EXISTS assignment (
                assign_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id      INTEGER NOT NULL,
                tg_id        INTEGER NOT NULL,      -- волонтёр
                assigned_by  INTEGER NOT NULL,      -- админ
                assigned_at  TEXT    NOT NULL,
                status       TEXT    NOT NULL,
                FOREIGN KEY(task_id)     REFERENCES task(task_id),
                FOREIGN KEY(tg_id)       REFERENCES users(tg_id),
                FOREIGN KEY(assigned_by) REFERENCES users(tg_id)
            )
        ''')

        # (Опционально) лог аудита
        await db.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT    NOT NULL,
                operation  TEXT    NOT NULL,
                record_id  INTEGER,
                timestamp  TEXT    NOT NULL,
                details    TEXT
            )
        ''')

        await db.commit()


async def main():
    await create_database()

asyncio.run(main())