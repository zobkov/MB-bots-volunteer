from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from aiogram import Bot
from typing import Dict, Any


scheduler = AsyncIOScheduler()
scheduler.start()

# title, description, start, end 
class Scheduler():
    def __init__(self, bot: Bot, ):
        self.bot = bot
        self.scheduler =  AsyncIOScheduler()
        self.scheduler.start()
    
    def add(self, opening_func: function, closing_func: function, run_date: datetime, close_date: datetime, task_param: Dict[str, Any], trigger: str ='date', closing: bool = True):
        
        # opening part 
        self.scheduler.add_job(
            func= opening_func, # opening function. It needs to change status in the db and send messages to users according to a filter
            trigger= trigger,
            run_date= run_date,
            args= [task_param['role'], task_param['text']]
        )

        if not closing:
            return 
        
        # closing part 
        self.scheduler.add_job(
            func= closing_func, # closing function. It needs to change task's status in the db and send messages to users according to filter 
            trigger= trigger,
            run_date= close_date,
            args= [task_param['role'], task_param['text']]
        )


class Schedule():
    pass 
