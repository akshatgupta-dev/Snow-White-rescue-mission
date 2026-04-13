from src.game_foundation import (
    SCENE_KIRJURINLUOTO,
    SCENE_FINAL,
    STATE_BEAR_ALLOWED_PASSAGE,
    STATE_QUEEN_DEFEATED,
    get_flag,
    set_flag,
    damage_player,
    has_item,
    ITEM_LIGHTSABER,
)


def get_kirjurinluoto_intro():
    return {
        "prompt_type": "scene_intro",
        "scene_id": SCENE_KIRJURINLUOTO,
        "scene_facts": [
            "Cinderella enters Kirjurinluoto.",
            "The park is covered in thick fog and strange magic.",
            "False paths twist through the landscape, making every direction feel uncertain.",
            "Somewhere ahead, the Evil Queen is waiting on her stage.",
            "To move forward, Cinderella must find the true path through illusion.",
        ],
    }


def get_kirjurinluoto_actions(state):
    return [
        {
            "action_id": "inspect_fog",
            "label": "Study the fog and the paths",
            "input_required": False,
        },
        {
            "action_id": "listen",
            "label": "Listen carefully for clues",
            "input_required": False,
        },
        {
            "action_id": "choose_left",
            "label": "Take the left path",
            "input_required": False,
        },
        {
            "action_id": "choose_center",
            "label": "Take the center path",
            "input_required": False,
        },
        {
            "action_id": "choose_right",
            "label": "Take the right path",
            "input_required": False,
        },
    ]


def handle_kirjurinluoto_action(state, action_id, user_input=None):
    if not get_flag(state, STATE_BEAR_ALLOWED_PASSAGE):
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_KIRJURINLUOTO,
            "scene_facts": [
                "The crossing into Kirjurinluoto is not truly open to Cinderella yet.",
                "Without the guardian's trust, the deeper magic of the park resists her.",
            ],
            "next_scene": None,
        }

    if action_id == "inspect_fog":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_KIRJURINLUOTO,
            "scene_facts": [
                "The fog shifts constantly, but not evenly.",
                "The outer paths seem more eager to draw attention to themselves.",
                "The middle path feels less dramatic, but more real.",
            ],
            "next_scene": None,
        }

    if action_id == "listen":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_KIRJURINLUOTO,
            "scene_facts": [
                "Most of the park is filled with whispering illusion.",
                "But from somewhere ahead, Cinderella can sense a steadier silence at the center.",
                "The truth here feels quieter than the traps around it.",
            ],
            "next_scene": None,
        }

    if action_id in {"choose_left", "choose_right"}:
        damage_player(state, 10)
        chosen_side = "left" if action_id == "choose_left" else "right"
        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_KIRJURINLUOTO,
            "scene_facts": [
                f"Cinderella takes the {chosen_side} path.",
                "The way twists into illusion almost immediately.",
                "The fog closes around her and drains her strength before pushing her back.",
                "The true way forward still lies ahead somewhere.",
            ],
            "next_scene": None,
        }

    if action_id == "choose_center":
        if not has_item(state, ITEM_LIGHTSABER):
            state.current_scene = SCENE_FINAL
            return {
                "prompt_type": "success_transition",
                "scene_id": SCENE_KIRJURINLUOTO,
                "scene_facts": [
                    "Cinderella stays calm and follows the center path through the fog.",
                    "The illusions weaken as she moves forward.",
                    "At the heart of Kirjurinluoto, she reaches the Evil Queen's stage.",
                    "But she has come without the weapon she was meant to earn first.",
                ],
                "next_scene": SCENE_FINAL,
            }

        state.current_scene = SCENE_FINAL
        return {
            "prompt_type": "success_transition",
            "scene_id": SCENE_KIRJURINLUOTO,
            "scene_facts": [
                "Cinderella stays calm and follows the center path through the fog.",
                "The false paths fall away behind her.",
                "At the heart of Kirjurinluoto, the Evil Queen's stage rises out of the mist.",
                "The final confrontation is now in front of her.",
            ],
            "next_scene": SCENE_FINAL,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_KIRJURINLUOTO,
        "scene_facts": [
            "Cinderella pauses in the fog, trying to separate illusion from truth.",
        ],
        "next_scene": None,
    }