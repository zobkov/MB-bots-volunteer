LEXICON_RU: dict[str, str] = {
    'no_answer':            'Данный тип апдейтов не поддерживается',
    'main_menu':            'это главное меню',
    'task_list':            "это меню всех заданий",
    'assignment_list':      "это меню всех назначений",
    'main':   "Это главное меню!!\nТут можно посмотреть что да как тут!!!",
    'main.tasks':               "Task list",
    'main.assignments':         "Assignments list",
    'main.assignments.list':    "Current assignments",
    'main.support':             "Support",
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
    'main.tasks':               "Task list",
    'main.assignments':         "Assignments list",
    'main.assignments.list':    "Current assignments",
    'main.support':             "Support",
    'main.tasks.list':          "Current tasks",
    'main.tasks.create_task':   "Create a task",
    'main.assignments.create_assignemnt':   "Create an assignment"
}

LEXICON_COMMANDS_RU: dict[str, str] = {
    '/start': 'Запуск бота',
    '/help': 'Справка',
    '/change_roles': 'Switch admin<->volunteer',
    '/main_menu': "Главное меню",
    '/add_user': "/add_user {username} {role}",
    '/set_debug_time': "/set_debug_time 1 12:30",
    '/debug_status': "Show debug info"
}