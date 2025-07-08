# MB-bots-volunteer
Таск менджмент для волонтеров конференции Менеджмент Будущего 
## Основные функции
- **Добавление пользователей** по юзернейму телеграмма
- **Разделение на роли**: Админ и Волонтер 
- **Управление заданиями**: добавление, просмотр, редактирование, удаление 
- **Назначение волонтеров на задания**
- **Управление срочными заданиями**: создание, рассылка волонтерам, уведомления об ответе админу, ручное и автоматическое удаление (спустя время, по умолчанию 30 минут) 
- **Синхронизация с Google Sheets**: ручная синхронизация в обе стороны БД<->Google Sheets. Задания, назначения и волонтеры отдельно. 
- **Уведомления волонтерам** 



## Структура БД
```mermaid
erDiagram
    users {
        BIGINT tg_id PK
        TEXT tg_username "UNIQUE"
        TEXT name
        TEXT role
    }
    pending_users {
        TEXT tg_username PK
        TEXT name
        TEXT role
    }
    task {
        SERIAL task_id PK
        TEXT title "UNIQUE"
        TEXT description
        INTEGER start_day
        TEXT start_time
        INTEGER end_day
        TEXT end_time
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP completed_at
    }
    assignment {
        SERIAL assign_id PK
        INTEGER task_id FK
        BIGINT tg_id FK
        BIGINT assigned_by FK
        TIMESTAMP assigned_at
        INTEGER start_day
        TEXT start_time
        INTEGER end_day
        TEXT end_time
        TEXT status
        BOOLEAN notification_scheduled
    }
    audit_log {
        SERIAL log_id PK
        TEXT table_name
        TEXT operation
        INTEGER record_id
        TIMESTAMP timestamp
        TEXT details
    }
    spot_task {
        SERIAL spot_task_id PK
        TEXT name
        TEXT description
        TIMESTAMP created_at
        TIMESTAMP expires_at
    }
    spot_task_response {
        SERIAL response_id PK
        INTEGER spot_task_id FK
        BIGINT volunteer_id FK
        VARCHAR response
        TIMESTAMP responded_at
        INTEGER message_id
    }
    users ||--o{ assignment : "has assignments"
    users ||--o{ assignment : "can assign"
    users ||--o{ spot_task_response : "responds to"
    task ||--o{ assignment : "is assigned in"
    spot_task ||--o{ spot_task_response : "has responses"
```
