from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
import asyncio
import logging

logger = logging.getLogger(__name__)

async def delete_spot_message(bot_token: str, chat_id: int, message_id: int):
    bot = Bot(token=bot_token)
    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramBadRequest as e:
        logger.error(f"Can't delete message {message_id} (chat_id={chat_id}): {e}")
    except Exception as e:
        logger.error(f"Can't delete message {message_id} (chat_id={chat_id}): {e}")
    finally:
        await bot.session.close()