from src.game_foundation import (
    SCENE_FINAL,
    ITEM_LIGHTSABER,
    ITEM_APPLE,
    STATE_QUEEN_DEFEATED,
    STATE_SNOW_WHITE_RESCUED,
    STATE_ATE_APPLE,
    has_item,
    add_item,
    remove_item,
    set_flag,
    get_flag,
    damage_player,
    heal_player,
)


def get_final_intro():
    return {
        "prompt_type": "scene_intro",
        "scene_id": SCENE_FINAL,
        "scene_facts": [
            "Cinderella arrives at the Evil Queen's stage in the heart of Kirjurinluoto.",
            "The Queen is waiting there as if the entire night has been building toward this performance.",
            "Dark magic hangs around the stage and the final chamber beyond it.",
            "Somewhere past the Queen, Snow White is still trapped inside enchantment.",
        ],
    }


def get_final_actions(state):
    if not get_flag(state, STATE_QUEEN_DEFEATED):
        return [
            {
                "action_id": "attack",
                "label": "Attack the Evil Queen",
                "input_required": False,
            },
            {
                "action_id": "defend",
                "label": "Defend against her magic",
                "input_required": False,
            },
            {
                "action_id": "talk",
                "label": "Try to talk to the Evil Queen",
                "input_required": False,
            },
        ]

    if not get_flag(state, STATE_SNOW_WHITE_RESCUED):
        return [
            {
                "action_id": "free_snow_white",
                "label": "Break the spell and free Snow White",
                "input_required": False,
            }
        ]

    actions = []

    if has_item(state, ITEM_APPLE):
        actions.extend([
            {
                "action_id": "eat_apple",
                "label": "Eat the apple",
                "input_required": False,
            },
            {
                "action_id": "leave_apple",
                "label": "Leave the apple alone",
                "input_required": False,
            },
        ])
    else:
        actions.extend([
            {
                "action_id": "inspect_apple",
                "label": "Inspect the apple",
                "input_required": False,
            },
            {
                "action_id": "eat_apple",
                "label": "Eat the apple",
                "input_required": False,
            },
            {
                "action_id": "leave_apple",
                "label": "Leave the apple alone",
                "input_required": False,
            },
        ])

    return actions


def handle_final_action(state, action_id, user_input=None):
    if not get_flag(state, STATE_QUEEN_DEFEATED):
        return _handle_queen_battle(state, action_id)

    if not get_flag(state, STATE_SNOW_WHITE_RESCUED):
        return _handle_rescue(state, action_id)

    return _handle_ending(state, action_id)


def _handle_queen_battle(state, action_id):
    if not has_item(state, ITEM_LIGHTSABER):
        damage_player(state, state.health)
        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_FINAL,
            "scene_facts": [
                "Cinderella faces the Evil Queen without the lightsaber.",
                "She has reached the final stage unprepared for the confrontation.",
                "Without the weapon earned in Agora Hall, she cannot break through the Queen's power.",
            ],
            "next_scene": None,
            "game_over": True,
        }

    if action_id == "attack":
        set_flag(state, STATE_QUEEN_DEFEATED, True)
        return {
            "prompt_type": "success_transition",
            "scene_id": SCENE_FINAL,
            "scene_facts": [
                "Cinderella attacks with the lightsaber.",
                "The Evil Queen's magic breaks under the strike.",
                "The stage loses its dark hold over the park.",
                "The path to Snow White is finally open.",
            ],
            "next_scene": None,
        }

    if action_id == "defend":
        damage_player(state, 5)

        if state.health <= 0:
            return {
                "prompt_type": "penalty_event",
                "scene_id": SCENE_FINAL,
                "scene_facts": [
                    "Cinderella blocks a wave of dark magic, but the strain is too much.",
                    "She collapses before she can finish the fight.",
                ],
                "next_scene": None,
                "game_over": True,
            }

        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_FINAL,
            "scene_facts": [
                "Cinderella defends against the Queen's magic.",
                "She avoids the worst of the attack, but the effort drains her strength.",
                "The confrontation is not over yet.",
            ],
            "next_scene": None,
        }

    if action_id == "talk":
        damage_player(state, 10)

        if state.health <= 0:
            return {
                "prompt_type": "penalty_event",
                "scene_id": SCENE_FINAL,
                "scene_facts": [
                    "Cinderella tries to reason with the Evil Queen.",
                    "The Queen responds with contempt and immediate violence.",
                    "The hesitation costs Cinderella everything.",
                ],
                "next_scene": None,
                "game_over": True,
            }

        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_FINAL,
            "scene_facts": [
                "Cinderella tries to talk instead of striking.",
                "The Evil Queen is not interested in peace or delay.",
                "Her attack lands while Cinderella hesitates.",
            ],
            "next_scene": None,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_FINAL,
        "scene_facts": [
            "The Evil Queen waits at the center of the stage.",
            "The final confrontation cannot be avoided.",
        ],
        "next_scene": None,
    }


def _handle_rescue(state, action_id):
    if action_id != "free_snow_white":
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_FINAL,
            "scene_facts": [
                "Snow White is still trapped inside fading magic.",
                "Cinderella only needs to reach out and break the spell.",
            ],
            "next_scene": None,
        }

    set_flag(state, STATE_SNOW_WHITE_RESCUED, True)

    if not has_item(state, ITEM_APPLE):
        add_item(state, ITEM_APPLE)

    return {
        "prompt_type": "success_transition",
        "scene_id": SCENE_FINAL,
        "scene_facts": [
            "Cinderella breaks the spell holding Snow White in place.",
            "Snow White is finally free.",
            "The rescue is complete at last.",
            "After the emotional reunion, both of them immediately realize how hungry they are.",
            "Nearby, a beautiful apple catches the light.",
        ],
        "next_scene": None,
    }


def _handle_ending(state, action_id):
    if action_id == "inspect_apple":
        if not has_item(state, ITEM_APPLE):
            add_item(state, ITEM_APPLE)

        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_FINAL,
            "scene_facts": [
                "The apple looks shiny, fresh, and surprisingly ordinary after everything else that has happened.",
                "For once, the final choice feels simple.",
            ],
            "next_scene": None,
        }

    if action_id == "eat_apple":
        if has_item(state, ITEM_APPLE):
            remove_item(state, ITEM_APPLE)

        set_flag(state, STATE_ATE_APPLE, True)
        heal_player(state, 20)

        return {
            "prompt_type": "success_transition",
            "scene_id": SCENE_FINAL,
            "scene_facts": [
                "Cinderella and Snow White share the apple.",
                "The fruit restores Cinderella's strength after the long night.",
                "They leave Kirjurinluoto together feeling safer, steadier, and less hungry.",
                "The story ends with a simple lesson about kindness, effort, and healthy choices.",
            ],
            "next_scene": None,
            "game_complete": True,
        }

    if action_id == "leave_apple":
        return {
            "prompt_type": "success_transition",
            "scene_id": SCENE_FINAL,
            "scene_facts": [
                "Cinderella decides to leave the apple alone.",
                "Snow White is still rescued, and the long night is still over.",
                "Together they leave Kirjurinluoto safely, carrying the lesson of the journey with them.",
            ],
            "next_scene": None,
            "game_complete": True,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_FINAL,
        "scene_facts": [
            "The danger has passed.",
            "Only the final choice remains.",
        ],
        "next_scene": None,
    }