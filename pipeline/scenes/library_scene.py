from src.game_foundation import (
    SCENE_LIBRARY,
    SCENE_AGORA,
    ITEM_MAP,
    STATE_HAS_MAP,
    add_item,
    set_flag,
    get_flag,
    damage_player,
)


def get_library_intro():
    return {
        "prompt_type": "scene_intro",
        "scene_id": SCENE_LIBRARY,
        "scene_facts": [
            "Cinderella arrives at the SAMK library late at night.",
            "The library is silent, dusty, and dimly lit.",
            "A magical holographic guardian blocks the entrance.",
            "The guardian will only allow passage if Cinderella proves she belongs here.",
            "A glowing map of Pori waits somewhere beyond the test.",
        ],
    }


def get_library_actions(state):
    if get_flag(state, STATE_HAS_MAP):
        return [
            {
                "action_id": "move_to_agora",
                "label": "Continue to Agora Hall",
                "input_required": False,
            }
        ]

    return [
        {
            "action_id": "inspect_guardian",
            "label": "Study the guardian",
            "input_required": False,
        },
        {
            "action_id": "inspect_library",
            "label": "Look around the library",
            "input_required": False,
        },
        {
            "action_id": "answer_question",
            "label": "Answer the guardian's question",
            "input_required": True,
            "input_hint": "Type what SAMK stands for.",
        },
    ]


def handle_library_action(state, action_id, user_input=None):
    if get_flag(state, STATE_HAS_MAP):
        if action_id == "move_to_agora":
            state.current_scene = SCENE_AGORA
            return {
                "prompt_type": "success_transition",
                "scene_id": SCENE_LIBRARY,
                "scene_facts": [
                    "With the map secured, Cinderella leaves the library behind.",
                    "The next clue points her toward Agora Hall.",
                ],
                "next_scene": SCENE_AGORA,
            }

        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_LIBRARY,
            "scene_facts": [
                "The trial here is already complete.",
                "There is nothing left in the library except the path forward.",
            ],
            "next_scene": None,
        }

    if action_id == "inspect_guardian":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_LIBRARY,
            "scene_facts": [
                "The guardian looks ancient, formal, and deeply unimpressed.",
                "Its magic seems tied to rules, knowledge, and rightful belonging.",
                "This feels less like a trick and more like a test of whether Cinderella knows where she is.",
            ],
            "next_scene": None,
        }

    if action_id == "inspect_library":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_LIBRARY,
            "scene_facts": [
                "Shelves stretch into the dimness around Cinderella.",
                "Everything in the room feels official, quiet, and academic.",
                "One dusty section of local folklore mentions old guardians near crossings who accepted seasonal offerings instead of force.",
                "Autumn gifts, especially pumpkin, are mentioned more than once.",
                "The challenge seems connected to the identity of the school itself.",
            ],
            "next_scene": None,
        }

    if action_id == "answer_question":
        answer = (user_input or "").strip().lower()

        if "satakunta university of applied sciences" in answer:
            add_item(state, ITEM_MAP)
            set_flag(state, STATE_HAS_MAP, True)

            return {
                "prompt_type": "success_transition",
                "scene_id": SCENE_LIBRARY,
                "scene_facts": [
                    "Cinderella answers correctly.",
                    "The guardian acknowledges her wisdom and steps aside.",
                    "A glowing map of Pori is revealed.",
                    "Cinderella takes the map.",
                    "The clue ahead points toward Agora Hall.",
                ],
                "next_scene": None,
            }

        damage_player(state, 10)

        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_LIBRARY,
            "scene_facts": [
                "Cinderella gives the wrong answer.",
                "The guardian releases a burst of dark magical energy.",
                "The failed answer leaves her shaken and weaker.",
                "The library remains closed to her for now.",
            ],
            "next_scene": None,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_LIBRARY,
        "scene_facts": [
            "Cinderella pauses before the guardian's test.",
            "The library waits in complete silence.",
        ],
        "next_scene": None,
    } 