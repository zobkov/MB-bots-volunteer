from lexicon.lexicon_ru import LEXICON_RU_BUTTONS as LEXICON

admin_menu_structure: dict[str, list[tuple[str, str]]] = {
    "main": [
        (LEXICON["main.tasks"],         "main.tasks"),
        (LEXICON["main.volunteers"],     "main.volunteers"),
        (LEXICON["main.support"],       "main.support"),
        (LEXICON["main.sync"],       "main.sync")
    ],
    "main.tasks": [
        (LEXICON["main.tasks.create_task"],         "main.tasks.create_task"),
        (LEXICON["main.tasks.create_spot_task"],    "main.tasks.create_spot_task"),
        (LEXICON["main.tasks.list"],                "main.tasks.list"),
        (LEXICON["main.tasks.spot_list"],                "main.tasks.spot_list")
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
    ],
    "main.sync": [
        (LEXICON["main.sync.volunteers"],       "main.sync.volunteers"),
        (LEXICON["main.sync.tasks"],            "main.sync.tasks"),
        (LEXICON["main.sync.assignments"],      "main.sync.assignments")
    ],
    "main.sync.volunteers": [
        (LEXICON["to_google"], "main.sync.volunteers.to_google"),
        (LEXICON["from_google"], "main.sync.volunteers.from_google")
    ],
    "main.sync.tasks": [
        (LEXICON["to_google"], "main.sync.tasks.to_google"),
        (LEXICON["from_google"], "main.sync.tasks.from_google")
    ],
    "main.sync.assignments": [
        (LEXICON["to_google"], "main.sync.assignments.to_google"),     # Fixed path
        (LEXICON["from_google"], "main.sync.assignments.from_google")  # Fixed path
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