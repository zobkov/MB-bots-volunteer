from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime
from utils.event_time import EventTimeManager

router = Router()

@router.message(Command("debug_status"))
async def debug_status(message: Message, event_manager: EventTimeManager):
    """Показывает текущий статус времени"""
    current_time = event_manager.current_time
    current_day = event_manager.get_current_event_day()
    status = event_manager.get_current_status()
    
    await message.answer(
        f"Текущий статус:\n"
        f"{status}\n\n"
        f"Абсолютное время: {current_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"Debug mode: {'включен' if event_manager.debug_mode else 'выключен'}"
    )

@router.message(Command("set_debug_time"))
async def set_debug_time(message: Message, event_manager: EventTimeManager):
    """Устанавливает отладочное время. Формат: /set_debug_time <день> <ЧЧ:ММ>"""
    if not event_manager.debug_mode:
        await message.answer(
            "Debug mode не включен!\n"
            "Добавьте DEBUG_MODE=true в .env файл"
        )
        return

    try:
        # Format: /set_debug_time 2 14:30 (день 2, 14:30)
        _, day, time = message.text.split()
        day = int(day)
        
        # Проверяем формат времени
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            raise ValueError("Неверный формат времени")
            
        # Конвертируем в абсолютное время
        debug_time = event_manager.datetime_from_event_day(day, time)
        event_manager.set_debug_time(debug_time)
        
        # Получаем текущий статус
        status = event_manager.get_current_status()
        
        await message.answer(
            f"Отладочное время установлено!\n\n"
            f"Статус: {status}\n"
            f"Абсолютное время: {debug_time.strftime('%Y-%m-%d %H:%M')}"
        )
        
    except ValueError as e:
        await message.answer(
            f"Ошибка: {str(e)}\n\n"
            f"Формат: /set_debug_time <день> <ЧЧ:ММ>\n"
            f"Пример: /set_debug_time 2 14:30\n"
            f"День должен быть от 1 до {event_manager.days_count}"
        )
    except IndexError:
        await message.answer(
            "Неверный формат команды!\n\n"
            "Формат: /set_debug_time <день> <ЧЧ:ММ>\n"
            "Пример: /set_debug_time 2 14:30"
        )