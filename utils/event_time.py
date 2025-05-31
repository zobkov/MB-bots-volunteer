from datetime import datetime, timedelta
from typing import Optional, Tuple

class EventTimeManager:
    def __init__(self, start_date: datetime, days_count: int, debug_mode: bool = False):
        self.start_date = start_date
        self.days_count = days_count
        self.debug_mode = debug_mode
        self._debug_current_time: Optional[datetime] = None

    @property
    def current_time(self) -> datetime:
        """Returns current time or debug time if in debug mode"""
        if self.debug_mode and self._debug_current_time:
            return self._debug_current_time
        return datetime.now()

    def set_debug_time(self, debug_time: datetime) -> None:
        """Sets debug current time"""
        if self.debug_mode:
            self._debug_current_time = debug_time

    def get_event_day(self, dt: datetime = None) -> int:
        """Returns event day number (1-based) for given datetime or current time"""
        dt = dt or self.current_time
        delta = dt.date() - self.start_date.date()
        day_num = delta.days + 1
        if 1 <= day_num <= self.days_count:
            return day_num
        return 0  # Not during event

    def datetime_from_event_day(self, day: int, time: str) -> datetime:
        """Converts event day number and time to absolute datetime"""
        if not (1 <= day <= self.days_count):
            raise ValueError(f"Day must be between 1 and {self.days_count}")
        
        hour, minute = map(int, time.split(':'))
        return self.start_date + timedelta(days=day-1, hours=hour, minutes=minute)

    def event_day_from_datetime(self, dt: datetime) -> Tuple[int, str]:
        """Converts absolute datetime to event day number and time"""
        day = self.get_event_day(dt)
        if day == 0:
            raise ValueError("DateTime is outside event period")
        return day, dt.strftime("%H:%M")

    def is_valid_event_time(self, day: int, time: str) -> bool:
        """Checks if given event day and time are valid"""
        try:
            dt = self.datetime_from_event_day(day, time)
            return dt > self.current_time
        except ValueError:
            return False