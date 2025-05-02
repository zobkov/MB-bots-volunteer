
from aiogram.types import Message

from services.mailing.scheduler import Scheduler


from database.sqlite_model import get_by_filter, Task, User


async def opening_mail_function(message: Message, task: Task, conn=None, scheduler = None,):
    if conn and scheduler:
        # TODO 
        
        pass
    pass

async def closing_mail_function(message: Message, conn=None, scheduler = None):
    if conn and scheduler:
        pass
    pass