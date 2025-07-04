from lexicon.lexicon_ru import LEXICON_RU_BUTTONS as LEXICON

admin_menu_structure: dict[str, list[tuple[str, str]]] = {
    "main": [
        (LEXICON["main.tasks"],         "main.tasks"),
        (LEXICON["main.volunteers"],     "main.volunteers"),
        (LEXICON["main.support"],       "main.support"),
    ],
    "main.tasks": [
        (LEXICON["main.tasks.create_task"],         "main.tasks.create_task"),
        (LEXICON["main.tasks.create_spot_task"],    "main.tasks.create_spot_task"),
        (LEXICON["main.tasks.list"],                "main.tasks.list")
    ],
    "main.volunteers": [
        (LEXICON["main.volunteers.add_volunteer"], "main.volunteers.add_volunteer"),
        (LEXICON["main.volunteers.list"],         "main.volunteers.list")
    ],
    "main.volunteers.list": [
        (LEXICON["main.volunteers.active"],       "main.volunteers.list.active"),
        (LEXICON["main.volunteers.pending"],      "main.volunteers.list.pending")
    ],
    "main.support": [
    ]
}

user_menu_structure: dict[str, list[tuple[str, str]]] = {
    "vmain": [
        (LEXICON["vmain.mytasks"],   "vmain.mytasks"),
        (LEXICON["vmain.faq"],       "vmain.faq")
    ],
    "vmain.mytasks": [
        (LEXICON["vmain.mytasks.placeholder"], "vmain.mytasks.placeholder"),
    ],
    "vmain.faq": [
        
    ]
}