from datetime import datetime, timedelta
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from handlers.callbacks import NavigationCD

def get_calendar_keyboard(current_date: datetime = None) -> InlineKeyboardMarkup:
    if not current_date:
        current_date = datetime.now().replace(day=1)  # Start from 1st day of month
    else:
        current_date = current_date.replace(day=1)  # Ensure we're at start of month
    
    builder = InlineKeyboardBuilder()
    
    # Add month/year header
    builder.button(
        text=current_date.strftime("%B %Y"),
        callback_data="ignore"
    )
    
    # Add weekday headers
    for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
        builder.button(text=day, callback_data="ignore")
    
    # Calculate first day of month and number of days
    first_day = current_date
    # Get last day of current month
    if current_date.month == 12:
        last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
    num_days = last_day.day
    
    # Add blank buttons until first day
    start_weekday = first_day.weekday()
    for _ in range(start_weekday):
        builder.button(text=" ", callback_data="ignore")
    
    # Add day buttons
    today = datetime.now()
    for day in range(1, num_days + 1):
        date = current_date.replace(day=day)
        if date < today:
            builder.button(text=" ", callback_data="ignore")
        else:
            builder.button(
                text=str(day),
                callback_data=f"date_{date.strftime('%Y-%m-%d')}"
            )
    
    # Calculate remaining buttons needed to complete the last row
    total_buttons = start_weekday + num_days
    remaining_buttons = (7 - (total_buttons % 7)) % 7
    
    # Add remaining empty buttons
    for _ in range(remaining_buttons):
        builder.button(text=" ", callback_data="ignore")
    
    # Navigation buttons - improved month calculation
    prev_month = (current_date.replace(day=15) - timedelta(days=20)).replace(day=1)
    next_month = (current_date.replace(day=15) + timedelta(days=20)).replace(day=1)
    
    builder.button(
        text="◀️ Previous Month",
        callback_data=f"month_{prev_month.strftime('%Y-%m')}"
    )
    builder.button(
        text="Next Month ▶️",
        callback_data=f"month_{next_month.strftime('%Y-%m')}"
    )
    
    # Adjust layout
    num_rows = (total_buttons + remaining_buttons) // 7
    builder.adjust(1, 7, *([7] * num_rows), 2)
    
    return builder.as_markup()

def get_time_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Add time buttons in 2-hour intervals
    for hour in range(0, 24, 2):
        builder.button(
            text=f"{hour:02d}:00",
            callback_data=f"hour_{hour:02d}"
        )
        builder.button(
            text=f"{hour:02d}:30",
            callback_data=f"hour_{hour:02d}30"
        )
    
    builder.adjust(2)  # Two buttons per row
    return builder.as_markup()

def get_minute_keyboard(hour: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Add minute buttons in 15-minute intervals
    for minute in range(0, 60, 15):
        builder.button(
            text=f"{hour}:{minute:02d}",
            callback_data=f"time_{hour}:{minute:02d}"
        )
    
    # Add back button
    builder.button(
        text="◀️ Back to hours",
        callback_data="back_to_hours"
    )
    
    builder.adjust(2)  # Two buttons per row
    return builder.as_markup()