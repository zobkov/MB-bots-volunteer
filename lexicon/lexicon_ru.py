LEXICON_RU: dict[str, str] = {
    'no_answer':            'Данный тип апдейтов не поддерживается',
    'main_menu':            'это главное меню',
    'task_list':            "это меню всех заданий",
    'assignment_list':      "это меню всех назначений",
    'main':   "Главное меню админской стороны. \nДоступно: список заданий, добавление заданий, изменение заданий, назначение волонтеров",
    'main.tasks':               "Список заданий",
    'main.assignments':         "Assignments list",
    'main.assignments.list':    "Current assignments",
    'main.support':             (
                                "Если меню не вернулось после каких-то действий, то введи /start.\n"
                                "Если что-то зависло — введи /start\n\n"
                                "Для того, чтобы поменять назначение волонтеров на задачу, нажми на кнопку <b>Создать назначение</b>. "
                                "После этого нажми на каждого волонтера, который нужен.\n"
                                "<b>ВНИМАНИЕ!</b> После нажатия на <b>Создать назначение</b>, назначения всегда сбрасываются. "
                                "Так что нажимай на всех волонтеров повторно.\n\n"
                                "Чтобы добавить волонтера, нужно занести его юзернейм в список ожидания — чтобы система его пропустила: "
                                "<code>/add_user {username} {role('admin'/'volunteer')}</code>\n"
                                "Либо кнопка добавить волонтера в меню волонтеров — так надежнее."
                                "\n\n\nЛюбые вопросы: @zobko"
                                ),
    'main.tasks.list':          "Current tasks",
    'task_creation.title':      "Please enter the task title:",
    'task_creation.description':"Please enter task description:",
    'task_creation.start_date': "Select start date:",
    'task_creation.time_format':"Please enter time in format HH:MM (e.g. 09:30):",
    'task_creation.start_date': "Select end date:",
    'task_creation.invalid_time_format':"Invalid time format! Please use HH:MM format (e.g. 09:30):",
    'task_edit.not_found':    "Задание не найдено",
    'main.assignments.create_assignemnt' : "Создаем назначение",
    'assignments_list': 'Список назначений',
    'create_assignment': 'Создать назначение',
    'select_task_for_assignment': 'Выберите задание для назначения',
    'main.volunteers':          "Волонтеры",
    'main.volunteers.add_volunteer': "Добавить волонтера",
    'main.volunteers.list':     "Список волонтеров",
    'task_list.select_day': "Выберите день для просмотра заданий:",
    'task_list.day_tasks': "📋 Задания на день {}\n\n",
    'vmain': "Главное меню волонтера",
    'vmain.mytasks': "📋 Мои задания:\n\n{tasks}",
    'vmain.mytasks.empty': "У вас пока нет назначенных заданий",
    'vmain.task_details': "📋 Детали задания:\n\n{details}",
    'main.tasks.create_spot_task': "Создать срочное задание",
    'main.tasks.spot_list':     "Список срочных",
    'main.sync': "Выберите что нужно синхронизировать:",
    'main.sync.volunteers': "Синхронизация волонтеров:",
    'main.sync.tasks': "Синхронизация заданий:",
    'main.sync.assignments': "Синхронизация назначений:",
    'main.sync.volunteers.to_google': "Выгрузка волонтеров в Google таблицу...",
    'main.sync.volunteers.from_google': "Загрузка волонтеров из Google таблицы...",
    
    # Tasks sync subpaths
    'main.sync.tasks.to_google': "Выгрузка заданий в Google таблицу...",
    'main.sync.tasks.from_google': "Загрузка заданий из Google таблицы...",
    
    # Assignments sync subpaths
    'main.sync.assignments.to_google': "Выгрузка назначений в Google таблицу...",
    'main.sync.assignments.from_google': "Загрузка назначений из Google таблицы..."
}

LEXICON_RU_BUTTONS: dict[str, str] = {
    'main_menu':                "Главное меню",
    'go_back':                  "Назад",
    'task_list':                "Задания",
    'assignment_list':          "Назначения",
    'main.mytasks':             "My tasks",
    'main.spots':               "Spot tasks available",
    'main.faq':                 "FAQ",
    'main.mytasks.placeholder': "PLACEHOLDER FOR A TASK BUTTON",
    'main.faq.placeholder':     "PLACEHOLDER FOR A FAQ",
    'main.tasks':               "Список заданий",
    'main.assignments':         "Assignments list",
    'main.assignments.list':    "Current assignments",
    'main.support':             "Тех. поддержка",
    'main.tasks.list':          "Текущие задания",
    'main.tasks.create_task':   "Создать задание",
    'main.tasks.create_spot_task': "Создать срочное задание",
    'main.tasks.spot_list':     "Список срочных",
    'main.assignments.create_assignemnt':   "Create an assignment",
    'main.volunteers':          "Волонтеры",
    'main.volunteers.add_volunteer': "Добавить волонтера",
    'main.volunteers.list':     "Список волонтеров",
    'main.volunteers.active': "👥 Активные волонтеры",
    'main.volunteers.pending': "⏳ Волонтеры в ожидании",
    'volunteer.add.username': "Введите username пользователя (без @):",
    'volunteer.add.name': "Введите полное имя волонтера:",
    'volunteer.add.confirm': "Подтвердите добавление волонтера:\nUsername: @{}\nИмя: {}\n\nВсе верно?",
    'volunteer.add.success': "✅ Волонтер успешно добавлен",
    'volunteer.add.cancel': "❌ Добавление волонтера отменено",
    'go_back': "◀️ Назад",
    'select_day': "📅 Выбрать день",
    'vmain.mytasks':          "Мои задания",
    'vmain.faq':                    "FAQ",
    'vmain.mytasks.placeholder':    "PALCEHOLDER",
    'vmain.mytasks': "📋 Мои задания",
    'task_details': "👁 Подробнее",
    'go_back_to_tasks': "◀️ К списку заданий",
    'main.sync': "🔄 Синхронизация",
    'main.sync.volunteers': "👥 Волонтеры",
    'main.sync.tasks': "📋 Задания",
    'main.sync.assignments': "📌 Назначения",
    'to_google': "⬆️ Выгрузить в Google",
    'from_google': "⬇️ Загрузить из Google"
}

LEXICON_COMMANDS_RU: dict[str, str] = {
    '/start': 'Запуск бота',
    '/help': 'Справка',
    '/change_roles': 'Switch admin<->volunteer',
    '/main_menu': "Главное меню",
    '/add_user': "/add_user {username} {role}",
    '/set_debug_time': "/set_debug_time 1 12:30",
    '/debug_status': "Show debug info",
    '/debug_assign': "/debug_assign volunteer_id task_id - Create assignment for testing",
    '/import_tasks': "send .csv to import tasks and update old ones"
}

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