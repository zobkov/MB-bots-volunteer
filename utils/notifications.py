from datetime import timedelta, datetime
from database.pg_model import Assignment, Task
from utils.event_time import EventTimeManager, EventTime

async def restore_notifications(pool, scheduler, event_manager: EventTimeManager):
    """Restore notifications for all pending assignments"""
    pending_assignments = await Assignment.get_pending_notifications(pool)
    
    for assignment in pending_assignments:
        task = await Task.get_by_id(pool, assignment.task_id)
        if task:
            start_time = event_manager.to_absolute_time(
                EventTime(day=task.start_day, time=task.start_time)
            )
            notification_time = start_time - timedelta(minutes=5)
            
            if notification_time > datetime.now():
                scheduler.add_job(
                    'services.assignment_service:notify_volunteers',
                    'date',
                    run_date=notification_time,
                    args=[task.task_id],
                    id=f'notification_{assignment.assign_id}'
                )
                await Assignment.mark_notification_scheduled(pool, assignment.assign_id)