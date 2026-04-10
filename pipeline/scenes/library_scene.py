from game_foundation import (
    SCENE_LIBRARY,
    SCENE_AGORA,
    ITEM_MAP,
    STATE_HAS_MAP,
    add_item,
    set_flag,
    damage_player,
)


def get_library_intro():
    return {
        "prompt_type": "scene_intro",
        "scene_id": SCENE_LIBRARY,
        "scene_facts": [
            "Cinderella arrives at the SAMK library late at night.",
            "The building is silent, dusty, and dimly lit.",
            "A magical holographic guardian blocks the entrance.",
            "The guardian will only allow passage if she proves her wisdom.",
            "A map of Pori can be obtained here.",
        ],
    }


def get_library_actions(state):
    return [
        {
            "action_id": "answer_question",
            "label": "Answer the guardian's question",
            "input_required": True,
            "input_hint": "Type what SAMK stands for.",
        }
    ]


def handle_library_action(state, action_id, user_input=None):
    if action_id != "answer_question":
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_LIBRARY,
            "scene_facts": [
                "Cinderella hesitates in front of the guardian.",
                "The guardian waits patiently for an answer.",
            ],
            "next_scene": None,
        }

    answer = (user_input or "").strip().lower()

    # SUCCESS
    if "satakunta university of applied sciences" in answer:
        add_item(state, ITEM_MAP)
        set_flag(state, STATE_HAS_MAP, True)
        state.current_scene = SCENE_AGORA

        return {
            "prompt_type": "success_transition",
            "scene_id": SCENE_LIBRARY,
            "scene_facts": [
                "Cinderella answers correctly.",
                "The guardian acknowledges her wisdom and disappears.",
                "A glowing map of Pori appears.",
                "Cinderella takes the map.",
                "The way to Agora Hall opens.",
            ],
            "next_scene": SCENE_AGORA,
        }

    # FAILURE
    damage_player(state, 10)

    return {
        "prompt_type": "penalty_event",
        "scene_id": SCENE_LIBRARY,
        "scene_facts": [
            "Cinderella gives the wrong answer.",
            "The guardian releases a burst of dark magical energy.",
            "Cinderella is struck and loses strength.",
            "The guardian remains, blocking the way forward.",
        ],
        "next_scene": None,
    }