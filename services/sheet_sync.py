import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import logging
from typing import Dict, List, Tuple, Any
import asyncpg
from database.pg_model import Task, User, PendingUser, Assignment
from utils.event_time import EventTime

# Google Sheets API constants
SPREADSHEET_ID = '1K4IM47awiowoVE_DuY6AvBk0wBLRhNUmyIJBTIHXzcg'  
SHEET_NAME = "List"  # or "Tasks" - use whichever is correct for your spreadsheet
VOLUNTEER_SHEET_NAME = "Volunteers"
VOLUNTEER_RANGE = f"{VOLUNTEER_SHEET_NAME}!A2:C"  # A=tg_id, B=tg_username, C=name
logger = logging.getLogger(__name__)

ASSIGNMENT_START_COL = 'H'  # First column with assignments
ASSIGNMENT_END_COL = 'Z'    # Last column with assignments
ASSIGNMENT_RANGE = f"{SHEET_NAME}!{ASSIGNMENT_START_COL}2:{ASSIGNMENT_END_COL}"

ADMIN_TG_ID = 257026813  # Admin who performs sheet synchronization

def get_sheets_service(cred: dict):
    """Helper function to create Google Sheets service"""
    return build('sheets', 'v4', credentials=ServiceAccountCredentials.from_json_keyfile_dict(
        cred, 
        ['https://www.googleapis.com/auth/spreadsheets']
    ))

def task_dict_from_db(row) -> dict:
    return {
        "title": row["title"],
        "description": row["description"],
        "start_day": row["start_day"],
        "start_time": row["start_time"],
        "end_day": row["end_day"],
        "end_time": row["end_time"],
    }

def task_dict_from_sheet(row) -> dict:
    return {
        "title": row.get("title"),
        "description": row.get("description"),
        "start_day": int(row.get("start_day", 0)),
        "start_time": row.get("start_time"),
        "end_day": int(row.get("end_day", 0)),
        "end_time": row.get("end_time"),
    }

async def get_sheet_and_db(pool, cred: Dict[str, Any]) -> Tuple[gspread.Worksheet, List[Dict], List[Dict]]:
    """Get data from both Google Sheet and database"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(cred, scope)
        client = gspread.authorize(creds)
        sheet = client.open("vol_bot_tasks").worksheet("List")
        sheet_records = sheet.get_all_records()
        
        async with pool.acquire() as conn:
            db_rows = await conn.fetch("SELECT * FROM task")
        
        db_tasks = [task_dict_from_db(row) for row in db_rows]
        sheet_tasks = [task_dict_from_sheet(row) for row in sheet_records]
        
        return sheet, sheet_tasks, db_tasks
    except Exception as e:
        logger.error(f"Error in get_sheet_and_db: {e}")
        raise

async def sync_sheet_to_db(pool: asyncpg.Pool, cred: dict) -> str:
    try:
        service = get_sheets_service(cred)
        
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A2:G'  # This correctly uses SHEET_NAME="List"
        ).execute()
        
        rows = result.get('values', [])
        if not rows:
            return "❌ Нет данных в таблице"

        tasks_created = 0
        tasks_updated = 0
        
        for row in rows:
            row.extend([''] * (7 - len(row)))
            title, description, start_day, start_time, end_day, end_time, db_id = row
            
            if not title:
                continue
                
            try:
                existing_task = None
                if db_id:
                    existing_task = await Task.get_by_id(pool, int(db_id))
                
                if existing_task:
                    # Используем специальный метод для обновления из таблицы
                    await Task.update_from_sheet(
                        pool,
                        existing_task.task_id,
                        title=title,
                        description=description,
                        start_day=int(start_day),
                        start_time=start_time,
                        end_day=int(end_day),
                        end_time=end_time
                    )
                    tasks_updated += 1
                else:
                    # Создаем новую задачу
                    task = await Task.create(
                        pool,
                        title=title,
                        description=description,
                        start_event_time=EventTime(int(start_day), start_time),
                        end_event_time=EventTime(int(end_day), end_time)
                    )
                    tasks_created += 1
                    
                    # Update db_id in sheet
                    range_name = f'{SHEET_NAME}!G{rows.index(row) + 2}'
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=range_name,
                        valueInputOption='RAW',
                        body={'values': [[str(task.task_id)]]}
                    ).execute()
                    
            except Exception as e:
                logger.error(f"Error processing row {row}: {e}")
                continue

        return f"✅ Синхронизация завершена: {tasks_created} заданий создано, {tasks_updated} заданий обновлено"

    except Exception as e:
        logger.error(f"Sync error: {e}")
        return f"❌ Ошибка синхронизации: {str(e)}"

async def sync_db_to_sheet(pool: asyncpg.Pool, cred: dict) -> str:
    try:
        service = get_sheets_service(cred)
        
        tasks = await Task.get_all(pool)
        values = []
        for task in tasks:
            values.append([
                task.title,
                task.description,
                str(task.start_day),
                task.start_time,
                str(task.end_day),
                task.end_time,
                str(task.task_id)
            ])
            
        # Update ranges to use correct sheet name
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A2:G'  # Use SHEET_NAME constant
        ).execute()
        
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A2',  # Use SHEET_NAME constant
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        return f"✅ Успешно синхронизировано {len(tasks)} заданий в таблицу"
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return f"❌ Ошибка синхронизации: {str(e)}"

async def sync_volunteers_sheet_to_db(pool: asyncpg.Pool, cred: dict) -> str:
    """Синхронизация волонтеров из Google таблицы в базу данных"""
    try:
        service = get_sheets_service(cred)
        
        # Get data from sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=VOLUNTEER_RANGE
        ).execute()
        
        rows = result.get('values', [])
        if not rows:
            return "❌ Нет данных о волонтерах в таблице"

        volunteers_created = 0
        volunteers_pending = 0
        volunteers_updated = 0
        
        for idx, row in enumerate(rows, start=2):  # start=2 because first row is header
            # Pad row with empty strings if needed
            row.extend([''] * (3 - len(row)))
            tg_id, tg_username, name = row
            
            # Skip empty rows
            if not tg_username:
                continue
                
            try:
                tg_username = tg_username.lstrip('@')  # Remove @ if present
                existing_user = None
                
                if tg_id:  # User with known TG ID
                    existing_user = await User.get_by_tg_id(pool, int(tg_id))
                else:
                    # Try to find user by username
                    existing_user = await User.get_by_username(pool, tg_username)
                    if existing_user:
                        # Update sheet with tg_id from database
                        range_name = f'{VOLUNTEER_SHEET_NAME}!A{idx}'
                        service.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=range_name,
                            valueInputOption='RAW',
                            body={'values': [[str(existing_user.tg_id)]]}
                        ).execute()
                
                if existing_user:
                    # Update existing user if needed
                    if (existing_user.name != name or 
                        existing_user.tg_username != tg_username):
                        await User.update(pool, existing_user.tg_id, 
                                       tg_username=tg_username, 
                                       name=name)
                        volunteers_updated += 1
                else:
                    if tg_id:
                        # Create new user if we have tg_id
                        await User.create(pool, int(tg_id), tg_username, name, 'volunteer')
                        volunteers_created += 1
                    else:
                        # Add to pending users if no tg_id found
                        await PendingUser.create(pool, tg_username, name, 'volunteer')
                        volunteers_pending += 1
                    
            except Exception as e:
                logger.error(f"Error processing volunteer row {row}: {e}")
                continue

        return f"✅ Синхронизация завершена: {volunteers_created} создано, {volunteers_updated} обновлено, {volunteers_pending} в ожидании"

    except Exception as e:
        logger.error(f"Volunteer sync error: {e}")
        return f"❌ Ошибка синхронизации: {str(e)}"

async def sync_volunteers_db_to_sheet(pool: asyncpg.Pool, cred: dict) -> str:
    """Синхронизация волонтеров из базы данных в Google таблицу"""
    try:
        service = get_sheets_service(cred)
        
        # Get all volunteer users from DB
        volunteers = await User.get_by_role(pool, 'volunteer')
        
        # Prepare data for sheet
        values = []
        for volunteer in volunteers:
            values.append([
                str(volunteer.tg_id),
                volunteer.tg_username,
                volunteer.name
            ])
            
        # Clear existing content
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=VOLUNTEER_RANGE
        ).execute()
        
        # Update sheet with new data
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{VOLUNTEER_SHEET_NAME}!A2",
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        return f"✅ Успешно синхронизировано {len(values)} волонтеров в таблицу"
        
    except Exception as e:
        logger.error(f"Volunteer sync error: {e}")
        return f"❌ Ошибка синхронизации: {str(e)}"

async def sync_assignments_sheet_to_db(pool: asyncpg.Pool, cred: dict) -> str:
    """Синхронизация назначений из Google таблицы в базу данных"""
    try:
        service = get_sheets_service(cred)
        
        # Get all data from sheet including assignments
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A2:Z'  # Get all columns
        ).execute()
        
        rows = result.get('values', [])
        if not rows:
            return "❌ Нет данных в таблице"

        assignments_created = 0
        tasks_updated = 0
        
        for row_idx, row in enumerate(rows, start=2):
            # Skip empty rows
            if not row:
                continue
                
            # Pad row with empty strings if needed
            row.extend([''] * (26 - len(row)))  # 26 columns total (A-Z)
            
            # Get task info
            task_id = row[6]  # Column G (db_id)
            if not task_id:
                continue
                
            try:
                task_id = int(task_id)
                assignees = [username for username in row[7:26] if username]  # Columns H-Z
                
                if assignees:
                    # Delete existing assignments for this task
                    await Assignment.delete_by_task(pool, task_id)
                    tasks_updated += 1
                    
                    # Create new assignments
                    task = await Task.get_by_id(pool, task_id)
                    if not task:
                        continue
                        
                    for username in assignees:
                        username = username.lstrip('@')
                        volunteer = await User.get_by_username(pool, username)
                        if volunteer:
                            await Assignment.create(
                                pool=pool,
                                task_id=task_id,
                                tg_id=volunteer.tg_id,
                                assigned_by=ADMIN_TG_ID,  # Use admin constant instead of 0
                                start_day=task.start_day,
                                start_time=task.start_time,
                                end_day=task.end_day,
                                end_time=task.end_time
                            )
                            assignments_created += 1
                    
            except Exception as e:
                logger.error(f"Error processing assignments for task {task_id}: {e}")
                continue

        return f"✅ Синхронизация завершена: {assignments_created} назначений создано для {tasks_updated} заданий"
    except Exception as e:
        logger.error(f"Assignment sync error: {e}")
        return f"❌ Ошибка синхронизации: {str(e)}"

async def sync_assignments_db_to_sheet(pool: asyncpg.Pool, cred: dict) -> str:
    """Синхронизация назначений из базы данных в Google таблицу"""
    try:
        service = get_sheets_service(cred)
        
        # Get all tasks from sheet to get their row numbers
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A2:G'
        ).execute()
        
        rows = result.get('values', [])
        if not rows:
            return "❌ Нет данных в таблице"
            
        # Create mapping of task_id to row_number
        task_row_map = {}
        for idx, row in enumerate(rows, start=2):
            if len(row) > 6 and row[6]:  # If has db_id
                task_row_map[int(row[6])] = idx
        
        tasks_updated = 0
        
        # Process each task that exists in the sheet
        for task_id, row_num in task_row_map.items():
            try:
                # Get assignments for this task
                assignments = await Assignment.get_by_task(pool, task_id)
                
                # Prepare usernames list
                usernames = []
                for assignment in assignments:
                    if assignment.status != 'cancelled':
                        volunteer = await User.get_by_tg_id(pool, assignment.tg_id)
                        if volunteer:
                            usernames.append(volunteer.tg_username)
                
                # Pad with empty strings to have 19 values
                usernames.extend([''] * (19 - len(usernames)))
                
                # Update sheet
                range_name = f'{SHEET_NAME}!H{row_num}:Z{row_num}'
                service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [usernames]}
                ).execute()
                
                tasks_updated += 1
                
            except Exception as e:
                logger.error(f"Error updating assignments for task {task_id}: {e}")
                continue

        return f"✅ Успешно синхронизированы назначения для {tasks_updated} заданий"
    except Exception as e:
        logger.error(f"Assignment sync error: {e}")
        return f"❌ Ошибка синхронизации: {str(e)}"