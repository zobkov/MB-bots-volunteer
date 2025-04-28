import logging
import asyncio

from config_data.config import load_config

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

API_TOKEN = load_config().tg_bot.token
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Храним задачи таймера по chat_id
tasks: dict[int, asyncio.Task] = {}

# Список вопросов с индивидуальным таймаутом
QUESTIONS = [
    {"text": "Что конференция может дать тебе? И что ты можешь дать конференции взамен? Подробно раскрой ответ.", "timeout": 180},
    {"text": "Какая в этом году тема конференции?", "timeout": 30},
    {"text": "Какой по счёту в этом году будет конференция? Укажи число.", "timeout": 15},
    {"text": "Когда будет проходить конференция? Укажи даты.", "timeout": 15},
    {"text": "Расположение аудиторий на 1-ом этаже. Укажи последовательность букв, которыми обозначены следующие аудитории: 1206, 1222, 1212, 1301, 1216, 1215.", "timeout": 90},
    {"text": "Расположение аудиторий на 2-ом этаже. Укажи последовательность букв, которыми обозначены следующие аудитории: 2222, 2229.", "timeout": 30},
]
# Фиксированное число шагов прогресс-бара
total_steps = 15

# Определяем состояния FSM
class Survey(StatesGroup):
    name = State()
    course = State()
    consent = State()
    question = State()

# Отрисовка прогресс-бара в текстовом виде
def render_bar(current_step: int, total_steps: int, elapsed: int, total: int) -> str:
    filled = '▰' * current_step
    empty = '▱' * (total_steps - current_step)
    return f"{filled}{empty} ({elapsed}/{total})"

# Функция запуска задачи прогресса с доступом к FSMContext
def run_progress(message: Message, steps: int, interval: float, total: int, state: FSMContext):
    async def _runner():
        chat_id = message.chat.id
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
        # Таймер истёк — очищаем и отправляем следующее
        tasks.pop(chat_id, None)
        await bot.send_message(chat_id, "⏰ Время вышло! Переходим к следующему вопросу.")
        data = await state.get_data()
        idx = data.get("q_idx", 0) + 1
        await state.update_data(q_idx=idx)
        await send_next_question(chat_id, state)
    return asyncio.create_task(_runner())

# Отправка вопроса и инициация таймера
async def send_next_question(chat_id: int, state: FSMContext):
    data = await state.get_data()
    idx = data.get("q_idx", 0)
    if idx >= len(QUESTIONS):
        await bot.send_message(chat_id, "✅ Опрос завершён! Спасибо за участие.")
        await state.clear()
        return

    q = QUESTIONS[idx]
    # Отправляем вопрос
    await bot.send_message(
        chat_id,
        f"Вопрос {idx+1} из {len(QUESTIONS)}:\n{q['text']}\n(Время на ответ: {q['timeout']} с.)"
    )
    # Отправляем прогресс-бар на 0 шагов
    bar_msg = await bot.send_message(
        chat_id,
        render_bar(0, total_steps, 0, q['timeout'])
    )
    # Сохраняем индекс и message_id таймера
    await state.update_data(q_idx=idx, timer_msg_id=bar_msg.message_id)
    # Отменяем старый таймер, если есть
    if chat_id in tasks:
        tasks[chat_id].cancel()
    # Запускаем новый с передачей контекста
    tasks[chat_id] = run_progress(bar_msg, total_steps, q['timeout']/total_steps, q['timeout'], state)

# Обработчик команды /start — вводная часть
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет, друг! Как тебя зовут? Напиши своё полное ФИО.")
    await state.set_state(Survey.name)

# Обработка ФИО
@dp.message(Survey.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("На каком ты курсе?")
    await state.set_state(Survey.course)

# Обработка курса
@dp.message(Survey.course)
async def process_course(message: Message, state: FSMContext):
    await state.update_data(course=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="consent_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="consent_no")],
    ])
    await message.answer("Подтверждаешь ли ты свое согласие на обработку персональных данных?", reply_markup=kb)
    await state.set_state(Survey.consent)

# Обработка согласия по callback
@dp.callback_query(lambda c: c.data and c.data.startswith("consent_"))
async def process_consent_callback(callback_query: CallbackQuery, state: FSMContext):
    consent_value = callback_query.data.split("consent_")[1]
    await state.update_data(consent=consent_value)
    # Убираем кнопки
    await callback_query.message.edit_text("Спасибо! Далее перейдём к общим вопросам.")
    await state.update_data(q_idx=0)
    await state.set_state(Survey.question)
    await send_next_question(callback_query.from_user.id, state)

# Обработка ответов на вопросы
@dp.message(Survey.question)
async def answer_question(message: Message, state: FSMContext):
    data = await state.get_data()
    idx = data.get("q_idx", 0)
    # Отменяем старый таймер
    if message.chat.id in tasks:
        tasks[message.chat.id].cancel()
        tasks.pop(message.chat.id, None)
    # Переходим к следующему вопросу
    await state.update_data(q_idx=idx+1)
    await send_next_question(message.chat.id, state)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
