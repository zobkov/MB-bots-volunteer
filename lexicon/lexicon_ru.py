# Main dictionary with all messages
LEXICON_RU: dict[str, str] = {
    # General messages
    'no_answer': 'Данный тип апдейтов не поддерживается',
    'main_menu': 'это главное меню',
    
    # Main menus
    'main': "Главное меню админской стороны. \nДоступно: список заданий, добавление заданий, изменение заданий, назначение волонтеров",
    'vmain': "Главное меню волонтера",
    
    # Tasks related messages
    'task_list': "это меню всех заданий",
    'task_list.select_day': "Выберите день для просмотра заданий:",
    'task_list.day_tasks': "📋 Задания на день {}\n\n",
    'task_creation.title': "Введите название задания:",
    'task_creation.description': "Введите описание задания:",
    'task_creation.start_date': "Выберите дату начала:",
    'task_creation.time_format': "Введите время в формате ЧЧ:ММ (например, 09:30):",
    'task_creation.invalid_time_format': "Неверный формат времени! Используйте формат ЧЧ:ММ (например, 09:30):",
    'task_edit.not_found': "Задание не найдено",
    'task_details': "👁 Подробнее",
    
    # Assignments related messages
    'assignment_list': "это меню всех назначений",
    'assignments_list': 'Список назначений',
    'create_assignment': 'Создать назначение',
    'select_task_for_assignment': 'Выберите задание для назначения',
    
    # Volunteer related messages
    'volunteer.add.username': "Введите username пользователя (без @):",
    'volunteer.add.name': "Введите полное имя волонтера:",
    'volunteer.add.confirm': "Подтвердите добавление волонтера:\nUsername: @{}\nИмя: {}\n\nВсе верно?",
    'volunteer.add.success': "✅ Волонтер успешно добавлен",
    'volunteer.add.cancel': "❌ Добавление волонтера отменено",
    
    # Navigation paths
    'main.tasks': "Список заданий",
    'main.tasks.list': "Текущие задания",
    'main.tasks.create_task': "Создать задание",
    'main.tasks.create_spot_task': "Создать срочное задание",
    'main.tasks.spot_list': "Список срочных",
    
    'main.assignments': "Список назначений",
    'main.assignments.list': "Текущие назначения",
    'main.assignments.create_assignemnt': "Создать назначение",
    
    'main.volunteers': "Волонтеры",
    'main.volunteers.list': "Список волонтеров",
    'main.volunteers.add_volunteer': "Добавить волонтера",
    'main.volunteers.active': "👥 Активные волонтеры",
    'main.volunteers.pending': "⏳ Волонтеры в ожидании",
    
    # Sync related messages
    'main.sync': "Выберите что нужно синхронизировать:",
    'main.sync.volunteers': "Синхронизация волонтеров:",
    'main.sync.tasks': "Синхронизация заданий:",
    'main.sync.assignments': "Синхронизация назначений:",
    'main.sync.volunteers.to_google': "Выгрузка волонтеров в Google таблицу...",
    'main.sync.volunteers.from_google': "Загрузка волонтеров из Google таблицы...",
    'main.sync.tasks.to_google': "Выгрузка заданий в Google таблицу...",
    'main.sync.tasks.from_google': "Загрузка заданий из Google таблицы...",
    'main.sync.assignments.to_google': "Выгрузка назначений в Google таблицу...",
    'main.sync.assignments.from_google': "Загрузка назначений из Google таблицы...",
    
    # Support
    'main.support': (
        "Если меню не вернулось после каких-то действий, то введи /start.\n"
        "Если что-то зависло — введи /start\n\n"
        "Основные инструкции находятся тут <a href=\"https://docs.google.com/document/d/152mH05Mab08GJzigIqi0cglMe32zzH4YwYoiC5QVnZo/edit?usp=sharing\">Google Docs</a>"
        "\n\n\nЛюбые вопросы: @zobko"
    ),
    
    # Volunteer interface messages
    'vmain.mytasks': "📋 Мои задания:\n\n{tasks}",
    'vmain.mytasks.empty': "У вас пока нет назначенных заданий",
    'vmain.task_details': "📋 Детали задания:\n\n{details}",
    'vmain.faq': "Здесь ты можешь выбрать вопрос и получить ответ. \nТакже можно просто написать в чат интересующий вопрос и бот постарается на него ответить (или отправит вопрос Даше 😅)"
}

# Button labels
LEXICON_RU_BUTTONS: dict[str, str] = {
    # Navigation buttons
    'main_menu': "Главное меню",
    'go_back': "◀️ Назад",
    'go_back_to_tasks': "◀️ К списку заданий",
    'select_day': "📅 Выбрать день",
    
    # Main menu buttons
    'main.sync': "🔄 Синхронизация",
    'main.tasks': "Список заданий",
    'main.volunteers': "Волонтеры",
    'main.support': "❓ FAQ",
    
    # Tasks buttons
    'task_list': "Задания",
    'main.tasks.list': "Текущие задания",
    'main.tasks.create_task': "Создать задание",
    'main.tasks.create_spot_task': "Создать срочное задание",
    'main.tasks.spot_list': "Список срочных",
    'task_details': "👁 Подробнее",
    
    # Assignment buttons
    'assignment_list': "Назначения",
    'main.assignments.list': "Текущие назначения",
    'main.assignments.create_assignemnt': "Создать назначение",
    
    # Volunteer buttons
    'main.volunteers.add_volunteer': "Добавить волонтера",
    'main.volunteers.list': "Список волонтеров",
    'main.volunteers.active': "👥 Активные волонтеры",
    'main.volunteers.pending': "⏳ Волонтеры в ожидании",
    
    # Sync buttons
    'main.sync.volunteers': "👥 Волонтеры",
    'main.sync.tasks': "📋 Задания",
    'main.sync.assignments': "📌 Назначения",
    'to_google': "⬆️ Выгрузить в Google",
    'from_google': "⬇️ Загрузить из Google",

    'vmain.mytasks': "📋 Мои задания",
    'vmain.faq': "❓ FAQ",
    'vmain.mytasks.placeholder': "Нет активных заданий"
}

# Command descriptions
LEXICON_COMMANDS_RU: dict[str, str] = {
    '/start': 'Запуск бота',
    '/help_admin': 'Справка',
    '/change_roles': 'Переключить admin<->volunteer',
    '/add_user': "/add_user {username} {role}",
    '/set_debug_time': "/set_debug_time 1 12:30",
    '/debug_status': "Показать отладочную информацию",
    '/debug_assign': "/debug_assign volunteer_id task_id - Создать назначение для тестирования",
    '/import_tasks': "Отправьте .csv для импорта и обновления заданий",
    '/faq_sync': "Синхронизация FAQ из Google таблицы",
    '/faq_status': "Проверка состояния FAQ",
    '/faq_config': "Проверка конфига FAQ"
}

# Volunteer-specific messages
LEXICON_VOLUNTEER_RU: dict[str, str] = {
    'add.username': "Введите username пользователя (без @):",
    'add.name': "Введите полное имя волонтера:",
    'add.confirm': "Подтвердите добавление волонтера:\nUsername: @{}\nИмя: {}\n\nВсе верно?",
    'add.success': "✅ Волонтер успешно добавлен",
    'add.cancel': "❌ Добавление волонтера отменено",
    'list.active': "👥 Активные волонтеры:\n\n{volunteers}",
    'list.pending': "⏳ Волонтеры в ожидании:\n\n{volunteers}",
    'list.empty': "Список пуст"
}