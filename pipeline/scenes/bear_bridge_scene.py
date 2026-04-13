from src.game_foundation import (
    SCENE_BEAR_BRIDGE,
    SCENE_KIRJURINLUOTO,
    ITEM_PUMPKIN,
    ITEM_CARRIAGE,
    STATE_HAS_HELPED_BEAR,
    STATE_BEAR_ALLOWED_PASSAGE,
    has_item,
    remove_item,
    set_flag,
    get_flag,
    transform_item,
    damage_player,
)


def get_bear_bridge_intro(state):
    intro_facts = [
        "Cinderella arrives near the bridge leading toward Kirjurinluoto.",
        "The night air is cold, and fog hangs over the crossing.",
        "A large bear sits near the bridge, crying quietly.",
        "The bear looks dangerous at first glance, but also miserable and weak.",
    ]

    if has_item(state, ITEM_CARRIAGE):
        transform_item(state, ITEM_CARRIAGE, ITEM_PUMPKIN)
        intro_facts.insert(
            0,
            "The magical carriage loses its power and transforms back into an ordinary pumpkin."
        )

    return {
        "prompt_type": "scene_intro",
        "scene_id": SCENE_BEAR_BRIDGE,
        "scene_facts": intro_facts,
    }


def get_bear_bridge_actions(state):
    if get_flag(state, STATE_BEAR_ALLOWED_PASSAGE):
        return [
            {
                "action_id": "cross_bridge",
                "label": "Cross the bridge into Kirjurinluoto",
                "input_required": False,
            }
        ]

    actions = [
        {
            "action_id": "inspect_bridge",
            "label": "Look closely at the bridge and the fog",
            "input_required": False,
        },
        {
            "action_id": "inspect_bear",
            "label": "Study the bear carefully",
            "input_required": False,
        },
        {
            "action_id": "talk_to_bear",
            "label": "Talk to the bear",
            "input_required": False,
        },
    ]

    if has_item(state, ITEM_PUMPKIN):
        actions.extend([
            {
                "action_id": "give_pumpkin",
                "label": "Give the pumpkin to the bear",
                "input_required": False,
            },
            {
                "action_id": "keep_pumpkin",
                "label": "Keep the pumpkin for yourself",
                "input_required": False,
            },
        ])

    return actions


def handle_bear_bridge_action(state, action_id, user_input=None):
    if get_flag(state, STATE_BEAR_ALLOWED_PASSAGE):
        if action_id == "cross_bridge":
            state.current_scene = SCENE_KIRJURINLUOTO
            return {
                "prompt_type": "success_transition",
                "scene_id": SCENE_BEAR_BRIDGE,
                "scene_facts": [
                    "The bear steps aside and allows Cinderella to pass.",
                    "The bridge opens into deeper fog and stranger magic.",
                    "Cinderella continues toward Kirjurinluoto, still hungry but now trusted.",
                ],
                "next_scene": SCENE_KIRJURINLUOTO,
            }

        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_BEAR_BRIDGE,
            "scene_facts": [
                "The way across the bridge is open now.",
                "The bear waits quietly, no longer an obstacle.",
            ],
            "next_scene": None,
        }

    if action_id == "inspect_bridge":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_BEAR_BRIDGE,
            "scene_facts": [
                "The bridge disappears into thick fog.",
                "The crossing feels guarded by more than wood and stone.",
                "This is clearly a threshold, and passage here must be earned.",
            ],
            "next_scene": None,
        }

    if action_id == "inspect_bear":
        return {
            "prompt_type": "hint_text",
            "scene_id": SCENE_BEAR_BRIDGE,
            "scene_facts": [
                "The bear is large enough to be dangerous, but too weak to feel truly threatening.",
                "Its posture is heavy with hunger and exhaustion.",
                "It seems less like a monster and more like a suffering guardian.",
            ],
            "next_scene": None,
        }

    if action_id == "talk_to_bear":
        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_BEAR_BRIDGE,
            "scene_facts": [
                "The bear admits that it is meant to guard the crossing.",
                "But hunger has left it too weak to do its duty properly.",
                "Its sadness feels genuine, and the bridge remains blocked.",
            ],
            "next_scene": None,
        }

    if action_id == "give_pumpkin":
        if has_item(state, ITEM_PUMPKIN):
            remove_item(state, ITEM_PUMPKIN)
            set_flag(state, STATE_HAS_HELPED_BEAR, True)
            set_flag(state, STATE_BEAR_ALLOWED_PASSAGE, True)

            return {
                "prompt_type": "success_transition",
                "scene_id": SCENE_BEAR_BRIDGE,
                "scene_facts": [
                    "Cinderella gives the pumpkin to the bear.",
                    "The bear brightens immediately and eats with grateful relief.",
                    "It reveals itself as the guardian of Pori and of this crossing.",
                    "Because Cinderella chose kindness, the way forward is opened to her.",
                ],
                "next_scene": None,
            }

        return {
            "prompt_type": "action_reaction",
            "scene_id": SCENE_BEAR_BRIDGE,
            "scene_facts": [
                "Cinderella has nothing she can offer the bear.",
            ],
            "next_scene": None,
        }

    if action_id == "keep_pumpkin":
        damage_player(state, 5)
        return {
            "prompt_type": "penalty_event",
            "scene_id": SCENE_BEAR_BRIDGE,
            "scene_facts": [
                "Cinderella keeps hold of the pumpkin instead of helping.",
                "The bear lowers its head in tired disappointment.",
                "The bridge remains blocked, and the cold fog seems to press in around her.",
                "The moment leaves her feeling weaker and less certain.",
            ],
            "next_scene": None,
        }

    return {
        "prompt_type": "action_reaction",
        "scene_id": SCENE_BEAR_BRIDGE,
        "scene_facts": [
            "Cinderella hesitates at the edge of the bridge.",
            "The bear waits in the fog.",
        ],
        "next_scene": None,
    }