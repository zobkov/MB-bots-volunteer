from datetime import datetime


# return datetime as a datetime object with the following format %Y-%m-%d %H:%M 

def datetime_format_str(date: str | datetime) -> str:
    if isinstance(date, datetime):
        formatted = date.isoformat(sep=" ",timespec='seconds')
    else:
        formatted = datetime.strptime(date, "%Y-%m-%d %H:%M").isoformat(sep=" ",timespec='seconds')
    
    return formatted


