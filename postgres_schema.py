import asyncio
import asyncpg

from config_data.config import load_config

async def create_tables(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        # Users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                tg_id        BIGINT PRIMARY KEY,
                tg_username  TEXT    UNIQUE NOT NULL,
                name        TEXT    NOT NULL,
                role        TEXT    NOT NULL
            )
        ''')

        # Updated Tasks table with relative dates
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS task (
                task_id      SERIAL PRIMARY KEY,
                title        TEXT    NOT NULL,
                description  TEXT,
                start_day    INTEGER NOT NULL,   -- День мероприятия (1-based)
                start_time   TEXT    NOT NULL,   -- Время в формате HH:MM
                end_day      INTEGER NOT NULL,   -- День мероприятия (1-based)
                end_time     TEXT    NOT NULL,   -- Время в формате HH:MM
                status       TEXT    NOT NULL,
                created_at   TIMESTAMP NOT NULL,
                updated_at   TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')

        # Updated Assignments table with relative dates
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS assignment (
                assign_id    SERIAL PRIMARY KEY,
                task_id      INTEGER NOT NULL REFERENCES task(task_id),
                tg_id        BIGINT NOT NULL REFERENCES users(tg_id),
                assigned_by  BIGINT NOT NULL REFERENCES users(tg_id),
                assigned_at  TIMESTAMP NOT NULL,
                start_day    INTEGER NOT NULL,
                start_time   TEXT NOT NULL,
                end_day      INTEGER NOT NULL,
                end_time     TEXT NOT NULL,
                status       TEXT NOT NULL
            )
        ''')

        # Audit log table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id      SERIAL PRIMARY KEY,
                table_name  TEXT NOT NULL,
                operation   TEXT NOT NULL,
                record_id   INTEGER,
                timestamp   TIMESTAMP NOT NULL,
                details     TEXT
            )
        ''')

async def main():
    config = load_config()

    try:
        pool = await asyncpg.create_pool(
            user=config.db.user,
            password=config.db.password,
            database=config.db.database,
            host=config.db.host,
            port=config.db.port
        )
        if pool:
            print("Successfully connected to PostgreSQL")
            await create_tables(pool)
            await pool.close()
        else:
            print("Failed to create connection pool")
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == '__main__':
    asyncio.run(main())