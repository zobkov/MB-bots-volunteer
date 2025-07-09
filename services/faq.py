import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import logging
import uuid
from typing import Dict, List, Optional
import asyncpg
from datetime import datetime

logger = logging.getLogger(__name__)

# Константы для Google Sheets FAQ
FAQ_SPREADSHEET_ID = '1IHsnFUID6tULoYeXLvDy5k0S7wRws8mSNqnJIaASZaA'  # ID вашей FAQ таблицы
FAQ_SHEET_NAME = "Bot_questions"  # Название листа с FAQ
FAQ_RANGE = f"{FAQ_SHEET_NAME}!A2:I"  # A=id, B=active, C=category, D=question, E=answer, F=keywords, G=updated_at, H=weight, I=notes

def get_faq_sheets_service(cred: dict):
    """Helper function to create Google Sheets service for FAQ"""
    return build('sheets', 'v4', credentials=ServiceAccountCredentials.from_json_keyfile_dict(
        cred, 
        ['https://www.googleapis.com/auth/spreadsheets']
    ))

class FAQService:
    def __init__(self, pool: asyncpg.Pool, cred: dict):
        self.pool = pool
        self.cred = cred
        
    async def sync_faq_from_google(self) -> str:
        """Синхронизация FAQ из Google таблицы в базу данных"""
        try:
            service = get_faq_sheets_service(self.cred)
            
            # Получаем данные из таблицы
            result = service.spreadsheets().values().get(
                spreadsheetId=FAQ_SPREADSHEET_ID,
                range=FAQ_RANGE
            ).execute()
            
            rows = result.get('values', [])
            logger.info(f"Retrieved {len(rows)} rows from Google Sheets")
            
            if not rows:
                # Если таблица пуста, удаляем все записи из БД
                deleted_count = await self._delete_all_faq_entries()
                return f"❌ Нет данных в FAQ таблице. Все записи удалены из БД ({deleted_count} записей)."

            new_questions = 0
            updated_questions = 0
            recreated_questions = 0
            
            # Сначала очищаем всю БД, чтобы избежать конфликтов
            await self._delete_all_faq_entries()
            logger.info("Cleared all existing FAQ entries from DB")
            
            # Теперь создаем все записи заново
            for row_idx, row in enumerate(rows, start=2):
                # Дополняем строку пустыми значениями если нужно
                row.extend([''] * (9 - len(row)))
                id_val, active, category, question, answer, keywords, updated_at, weight, notes = row
                
                logger.debug(f"Processing row {row_idx}: question='{question[:50]}...', answer='{answer[:50]}...'")
                
                # Пропускаем пустые строки
                if not question or not answer:
                    logger.debug(f"Skipping empty row {row_idx}: question='{question}', answer='{answer}'")
                    continue
                
                try:
                    # Преобразуем активность в boolean
                    is_active = str(active).lower() in ('true', '1', 'yes', 'да', 'активен')
                    
                    # Преобразуем вес в число
                    try:
                        weight_int = int(weight) if weight else 0
                    except ValueError:
                        weight_int = 0
                    
                    # Обрабатываем дату - если нет даты или она некорректная, используем сегодняшнюю
                    updated_date = datetime.now().date()
                    if updated_at:
                        try:
                            updated_date = datetime.strptime(updated_at, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                # Пробуем другие форматы даты
                                updated_date = datetime.strptime(updated_at, '%d.%m.%Y').date()
                            except ValueError:
                                # Если не получается распарсить, используем текущую дату
                                updated_date = datetime.now().date()
                    
                    # Форматируем дату для записи в таблицу
                    date_str = updated_date.strftime('%Y-%m-%d')
                    
                    if not id_val:
                        # Новый вопрос - создаем UUID и добавляем в БД
                        new_id = str(uuid.uuid4())
                        
                        await self._create_faq_entry(
                            new_id, is_active, category, question, 
                            answer, keywords, updated_date, weight_int, notes
                        )
                        
                        # Записываем UUID и дату обратно в таблицу
                        id_range = f'{FAQ_SHEET_NAME}!A{row_idx}'
                        date_range = f'{FAQ_SHEET_NAME}!G{row_idx}'
                        
                        # Обновляем ID
                        service.spreadsheets().values().update(
                            spreadsheetId=FAQ_SPREADSHEET_ID,
                            range=id_range,
                            valueInputOption='RAW',
                            body={'values': [[new_id]]}
                        ).execute()
                        
                        # Обновляем дату
                        service.spreadsheets().values().update(
                            spreadsheetId=FAQ_SPREADSHEET_ID,
                            range=date_range,
                            valueInputOption='RAW',
                            body={'values': [[date_str]]}
                        ).execute()
                        
                        new_questions += 1
                        logger.info(f"Created new FAQ entry with ID: {new_id}")
                        
                    else:
                        # Есть ID - создаем запись с этим ID
                        try:
                            await self._create_faq_entry(
                                id_val, is_active, category, question,
                                answer, keywords, updated_date, weight_int, notes
                            )
                            
                            # Обновляем дату синхронизации в таблице
                            date_range = f'{FAQ_SHEET_NAME}!G{row_idx}'
                            service.spreadsheets().values().update(
                                spreadsheetId=FAQ_SPREADSHEET_ID,
                                range=date_range,
                                valueInputOption='RAW',
                                body={'values': [[date_str]]}
                            ).execute()
                            
                            recreated_questions += 1
                            logger.info(f"Recreated FAQ entry with existing ID: {id_val}")
                        except Exception as e:
                            # Если не получается создать с существующим ID, создаем новый
                            logger.warning(f"Failed to create FAQ with existing ID {id_val}, creating new: {e}")
                            new_id = str(uuid.uuid4())
                            
                            await self._create_faq_entry(
                                new_id, is_active, category, question, 
                                answer, keywords, updated_date, weight_int, notes
                            )
                            
                            # Записываем новый UUID и дату в таблицу
                            id_range = f'{FAQ_SHEET_NAME}!A{row_idx}'
                            date_range = f'{FAQ_SHEET_NAME}!G{row_idx}'
                            
                            # Обновляем ID
                            service.spreadsheets().values().update(
                                spreadsheetId=FAQ_SPREADSHEET_ID,
                                range=id_range,
                                valueInputOption='RAW',
                                body={'values': [[new_id]]}
                            ).execute()
                            
                            # Обновляем дату
                            service.spreadsheets().values().update(
                                spreadsheetId=FAQ_SPREADSHEET_ID,
                                range=date_range,
                                valueInputOption='RAW',
                                body={'values': [[date_str]]}
                            ).execute()
                            
                            new_questions += 1
                            logger.info(f"Created FAQ entry with new ID: {new_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing FAQ row {row_idx}: {e}")
                    continue

            total_processed = new_questions + updated_questions + recreated_questions
            logger.info(f"FAQ sync completed: {new_questions} new, {updated_questions} updated, {recreated_questions} recreated, total: {total_processed}")

            result_parts = []
            if new_questions > 0:
                result_parts.append(f"{new_questions} новых")
            if updated_questions > 0:
                result_parts.append(f"{updated_questions} обновлено")
            if recreated_questions > 0:
                result_parts.append(f"{recreated_questions} синхронизировано")
            
            if result_parts:
                return f"✅ FAQ синхронизация завершена: {', '.join(result_parts)}"
            else:
                return "✅ FAQ синхронизация завершена: изменений нет"

        except Exception as e:
            logger.error(f"FAQ sync error: {e}")
            return f"❌ Ошибка синхронизации FAQ: {str(e)}"
    
    async def _create_faq_entry(self, id_val: str, active: bool, category: str, 
                               question: str, answer: str, keywords: Optional[str],
                               updated_at: datetime.date, weight: int, notes: Optional[str]):
        """Создание новой записи FAQ в БД"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO faq (id, active, category, question, answer, keywords, updated_at, weight, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, id_val, active, category, question, answer, keywords, updated_at, weight, notes)
    
    async def _delete_all_faq_entries(self) -> int:
        """Удаление всех записей FAQ из БД"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM faq")
            # Получаем количество удаленных записей из результата
            deleted_count = int(result.split()[-1]) if isinstance(result, str) and result.startswith("DELETE") else 0
            logger.info(f"Deleted all FAQ entries from DB: {deleted_count}")
            return deleted_count
    
    async def search_faq(self, query: str, limit: int = 5) -> List[Dict]:
        """Поиск в FAQ по запросу"""
        async with self.pool.acquire() as conn:
            # Используем полнотекстовый поиск
            results = await conn.fetch("""
                SELECT id, category, question, answer, weight
                FROM faq 
                WHERE active = true 
                  AND to_tsvector('russian', question || ' ' || coalesce(keywords, '') || ' ' || answer) 
                      @@ plainto_tsquery('russian', $1)
                ORDER BY weight DESC, 
                         ts_rank(to_tsvector('russian', question || ' ' || coalesce(keywords, '')), 
                                plainto_tsquery('russian', $1)) DESC
                LIMIT $2
            """, query, limit)
            
            return [dict(row) for row in results]
    
    async def get_faq_by_category(self, category: str) -> List[Dict]:
        """Получение FAQ по категории"""
        async with self.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, category, question, answer, weight
                FROM faq 
                WHERE active = true AND category = $1
                ORDER BY weight DESC, question
            """, category)
            
            return [dict(row) for row in results]
    
    async def get_all_categories(self) -> List[str]:
        """Получение всех активных категорий"""
        async with self.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT DISTINCT category 
                FROM faq 
                WHERE active = true 
                ORDER BY category
            """)
            
            return [row['category'] for row in results]