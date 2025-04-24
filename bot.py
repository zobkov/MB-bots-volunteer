import logging
import asyncio

from config import bot_token


from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router
from aiogram import F


bot = Bot(token=bot_token)
dp = Dispatcher()

# Словарь для хранения задач таймера по chat_id
tasks: dict[int, asyncio.Task] = {}

def render_bar(current_step: int, total_steps: int, elapsed: int, total: int) -> str:
    filled = '▰' * current_step
    empty = '▱' * (total_steps - current_step)
    return f"{filled}{empty} ({elapsed}/{total})"

async def run_progress(message: Message, steps: int, interval: float, chat_id: int, total: int):
    for i in range(1, steps + 1):
        try:
            await asyncio.sleep(interval)
            elapsed = int(i * interval)
            await bot.edit_message_text(
                render_bar(i, steps, elapsed, total),
                chat_id=chat_id,
                message_id=message.message_id
            )
        except asyncio.CancelledError:
            return
        except Exception:
            return

    # Таймер завершился
    tasks.pop(chat_id, None)
    await bot.send_message(chat_id, "⏰ Время вышло!")

@dp.message(Command("test"))
async def start_test(message: Message):
    duration = 60  # Общая длительность в секундах
    steps = 12     # Количество шагов прогресс-бара
    interval = duration / steps

    question = "Сколько будет 2+2?"
    await message.answer(question)

    # Отправляем начальный бар с 0 секунд
    bar_message = await message.answer(render_bar(0, steps, 0, duration))

    # Отменяем предыдущий таймер, если был
    if message.chat.id in tasks:
        tasks[message.chat.id].cancel()

    # Запускаем новый таймер
    task = asyncio.create_task(run_progress(bar_message, steps, interval, message.chat.id, duration))
    tasks[message.chat.id] = task

@dp.message()
async def handle_answer(message: Message):
    # Игнорируем команды
    if message.text and message.text.startswith("/"):
        return

    chat_id = message.chat.id
    if chat_id in tasks:
        tasks[chat_id].cancel()
        tasks.pop(chat_id, None)
        await message.answer("✅ Ответ получен, таймер остановлен.")
        # Здесь можно добавить логику перехода к следующему вопросу

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

