import asyncio
from database.pg_model import User, create_pool
from config_data.config import load_config



async def main():
    config = load_config()
    pool = await create_pool(
        user=config.db.user,
        password=config.db.password,
        database=config.db.database,
        host=config.db.host,
        port=config.db.port
    )
    
    # Test user creation
    await User.create(pool, 357026013, "volodya", "Volody Ivanov", "volunteer")
    await User.create(pool, 457016813, "anatoliy", "Anatoliy Vladimidov", "volunteer")
    
    # Test user retrieval
    result = await User.get_all(pool)
    for user in result:
        print(user.tg_username, user.name)
    
    await pool.close()

if __name__ == '__main__':
    asyncio.run(main())