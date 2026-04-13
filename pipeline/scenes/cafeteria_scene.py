from src.game_foundation import (
    SCENE_CAFETERIA,
    SCENE_BEAR_BRIDGE,
    ITEM_PUMPKIN,
    ITEM_CARRIAGE,
    STATE_HAS_CARRIAGE,
    add_item,
    has_item,
    transform_item,
    damage_player,
)


def get_cafeteria_intro():
    return {
        "prompt_type": "scene_intro",
        "scene_id": SCENE_CAFETERIA,
        "scene_facts": [
            "Cinderella enters the SAMK cafeteria late at night.",
            "The cafeteria is empty, silent, and strangely still.",
            "The overhead lights buzz softly.",
            "A single perfect pumpkin sits on a table in the middle of the room.",
            "The whole space feels like it is waiting for something.",
        ],
    }


def get_cafeteria_actions(state):
    if has_item(state, ITEM_CARRIAGE):
        return [
            {
                "action_id": "ride_carriage",
                "label": "Step into the magical carriage",
                "input_required": False,
            }
        ]

    if has_item(state, ITEM_PUMPKIN):
        return [
            {
                "action_id": "inspect_pumpkin",
                "label": "Inspect the pumpkin more closely",
                "input_required": False,
            },
            {
                "action_id": "listen",
                "label": "Listen to the quiet cafeteria",
                "input_required": False,
            },
            {
                "action_id": "wait",
                "label": "Wait and see what happens",
                "input_required": False,
            },
            {
                "action_id": "eat_pumpkin",
                "label": "Try to eat the pumpkin",
                "input_required": False,
            },
        ]

    return [
        {
            "action_id": "look_around",
            "label": "Look around the cafeteria",
            "input_required": False,
        },
        {
            "action_id": "inspect_tables",
            "label": "Inspect the empty tables and serving area",
            "input_required": False,
        },
        {
            "action_id": "listen",
            "label": "Listen carefully",
            "input_required": False,
        },
        {
            "action_id": "inspect_pumpkin",
            "label": "Inspect the pumpkin",
            "input_required": False,
        },
        {
            "action_id": "take_pumpkin",
            "label": "Take the pumpkin",
            "input_required": False,
        },
    ]


def handle_cafeteria_action(state, action_id, user_input=None):
    if has_item(state, ITEM_CARRIAGE):
        if action_id == "ride_carriage":
            state.current_scene = SCENE_BEAR_BRIDGE
            return {
                "prompt_type": "success_transition",
                "scene_id": SCENE_CAFETERIA,
                "scene_facts": [
                    "Cinderella steps into the magical carriage.",
                    "It begins to move as if it has been waiting for her all along.",
                    "The strange cafeteria disappears behind her as she is carried into the night.",
                ],
                "next_scene": SCENE_BEAR_BRIDGE,
            }

        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "The carriage waits silently for Cinderella to get in.",
            ],
            "next_scene": None,
        }

    if has_item(state, ITEM_PUMPKIN):
        return _handle_pumpkin_state(state, action_id)

    if action_id == "look_around":
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "The cafeteria is completely empty.",
                "No staff, students, or ordinary food remain.",
                "The pumpkin feels like the only important thing in the room.",
            ],
            "next_scene": None,
        }

    if action_id == "inspect_tables":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "The tables are abandoned and spotless.",
                "The serving area looks frozen, as if dinner ended hours ago.",
                "Everything ordinary has been stripped away, leaving only the pumpkin.",
            ],
            "next_scene": None,
        }

    if action_id == "listen":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "At first Cinderella hears only the low electric buzz of the lights.",
                "Then she notices the strange weight of the silence, as if time itself is holding its breath.",
                "The room feels like it is leading toward a magical moment.",
            ],
            "next_scene": None,
        }

    if action_id == "inspect_pumpkin":
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "The pumpkin looks unusually perfect.",
                "Its surface reflects the overhead lights with an unnatural glow.",
                "It seems edible, but not entirely meant for eating.",
            ],
            "next_scene": None,
        }

    if action_id == "take_pumpkin":
        add_item(state, ITEM_PUMPKIN)
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "Cinderella picks up the pumpkin.",
                "It feels heavier and warmer than expected.",
                "Her hunger immediately makes eating it feel like a very good idea.",
            ],
            "next_scene": None,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_CAFETERIA,
        "scene_facts": [
            "Cinderella lingers in the eerie cafeteria.",
            "The room remains silent around her.",
        ],
        "next_scene": None,
    }


def _handle_pumpkin_state(state, action_id):
    if action_id == "inspect_pumpkin":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "The pumpkin feels slightly unnatural in Cinderella's hands.",
                "Something about it suggests it is waiting for the right moment to change.",
                "It does not feel like ordinary food.",
            ],
            "next_scene": None,
        }

    if action_id == "listen":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "The cafeteria is so quiet that even the buzzing lights feel important.",
                "The air seems tense, as if a signal or deadline is approaching.",
                "Cinderella gets the sense that waiting might matter.",
            ],
            "next_scene": None,
        }

    if action_id == "wait":
        transform_item(state, ITEM_PUMPKIN, ITEM_CARRIAGE, STATE_HAS_CARRIAGE)
        return {
            "prompt_type": "success_transition",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "The stillness of the cafeteria suddenly breaks.",
                "An unseen clock strikes 10:00 PM.",
                "The pumpkin glows, shakes, and transforms into a magical carriage.",
                "Cinderella accepts the absurdity of the moment with tired disbelief.",
            ],
            "next_scene": None,
        }

    if action_id == "eat_pumpkin":
        damage_player(state, 5)
        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_CAFETERIA,
            "scene_facts": [
                "Cinderella tries to bite into the pumpkin.",
                "The taste is wrong, almost magically resistant.",
                "The experience leaves her slightly weaker and more confused.",
            ],
            "next_scene": None,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_CAFETERIA,
        "scene_facts": [
            "Cinderella pauses with the pumpkin in her hands.",
            "The room feels like it is waiting for her to understand something.",
        ],
        "next_scene": None,
    }