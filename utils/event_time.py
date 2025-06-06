from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Tuple

@dataclass
class EventTime:
    day: int      # День мероприятия (1-based)
    time: str     # Время в формате HH:MM

class EventTimeManager:
    def __init__(self, start_date: datetime, days_count: int, debug_mode: bool = False):
        self.start_date = start_date
        self.days_count = days_count
        self.debug_mode = debug_mode
        self._debug_current_time: datetime | None = None

    @property
    def current_time(self) -> datetime:
        """Возвращает текущее время или отладочное время если включен debug режим"""
        if self.debug_mode and self._debug_current_time:
            return self._debug_current_time
        return datetime.now()
    
    def set_debug_time(self, debug_time: datetime) -> None:
        """Устанавливает отладочное время"""
        if self.debug_mode:
            self._debug_current_time = debug_time

    def datetime_from_event_day(self, day: int, time: str) -> datetime:
        """Преобразует день мероприятия и время в абсолютную дату"""
        if not (1 <= day <= self.days_count):
            raise ValueError(f"Day must be between 1 and {self.days_count}")
        
        hour, minute = map(int, time.split(':'))
        return self.start_date + timedelta(days=day-1, hours=hour, minutes=minute)

    def get_current_event_day(self) -> int:
        """Возвращает текущий день мероприятия (1-based) или 0 если не во время мероприятия"""
        current = self.current_time
        delta = current.date() - self.start_date.date()
        day_num = delta.days + 1
        if 1 <= day_num <= self.days_count:
            return day_num
        return 0

    def to_absolute_time(self, event_time: EventTime) -> datetime:
        """Конвертирует относительное время мероприятия в абсолютное"""
        return self.datetime_from_event_day(event_time.day, event_time.time)

    def to_event_time(self, dt: datetime) -> EventTime:
        """Конвертирует абсолютное время в относительное время мероприятия"""
        delta = dt.date() - self.start_date.date()
        day = delta.days + 1
        
        if not (1 <= day <= self.days_count):
            raise ValueError("DateTime is outside event period")
            
        return EventTime(day=day, time=dt.strftime("%H:%M"))

    def is_valid_event_time(self, event_time: EventTime) -> bool:
        """Проверяет валидность времени мероприятия"""
        try:
            absolute_time = self.to_absolute_time(event_time)
            return absolute_time > self.current_time
        except ValueError:
            return False

    def get_current_status(self) -> str:
        """Возвращает текущий статус времени"""
        current = self.current_time
        current_day = self.get_current_event_day()
        
        if current_day == 0:
            if current < self.start_date:
                return "До начала мероприятия"
            else:
                return "После окончания мероприятия"
        
        return f"День {current_day} {current.strftime('%H:%M')}"