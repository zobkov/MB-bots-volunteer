from lexicon.lexicon_ru import LEXICON_RU_BUTTONS as LEXICON

admin_menu_structure: dict[str, list[tuple[str, str]]] = {
    "main": [
        (LEXICON["main.tasks"],         "main.tasks"),
        (LEXICON["main.assignments"],   "main.assignments"),
        (LEXICON["main.support"],       "main.support")
    ],
    "main.tasks": [
        (LEXICON["main.tasks.create_task"],     "main.tasks.create_task"),
        (LEXICON["main.tasks.list"],            "main.tasks.list"),
    ],
    "main.assignments": [
        (LEXICON["main.assignments.create_assignemnt"],     "main.assignments.create_assignemnt"),
        (LEXICON["main.assignments.list"],                  "main.assignments.list")
    ],
    "main.support": [
    ]
}

user_menu_structure: dict[str, list[tuple[str, str]]] = {
    "main": [
        (LEXICON["main.mytasks"],   "main.mytasks"),
        (LEXICON["main.spots"],     "main.spots"),
        (LEXICON["main.faq"],       "main.faq")
    ],
    "main.mytasks": [
        (LEXICON["main.mytasks.placeholder"], "main.mytasks.placeholder"),
    ],
    "main.faq": [
        (LEXICON["main.faq.placeholder"], "main.faq.placeholder")
    ]
}