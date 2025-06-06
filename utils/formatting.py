from database.pg_model import Task 


def format_task_time(task: Task) -> str:
    """
    Formats task time based on whether start and end days are the same.
    
    Args:
        task: Task object with start_day, start_time, end_day, end_time attributes
        
    Returns:
        str: Formatted time string
    """
    return (f"День {task.start_day} {task.start_time} - {task.end_time}"
            if task.start_day == task.end_day else
            f"День {task.start_day} {task.start_time} - День {task.end_day} {task.end_time}")