from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# scene names
SCENE_START = "start"
SCENE_LIBRARY = "library"
SCENE_AGORA = "agora_hall"
SCENE_CAFETERIA = "cafeteria"
SCENE_BEAR_BRIDGE = "bear_bridge"
SCENE_KIRJURINLUOTO = "kirjurinluoto"
SCENE_FINAL = "final"
DYNAMIC_SCENE = "dynamic_scene"

# item names
ITEM_MAP = "map"
ITEM_LIGHTSABER = "lightsaber"
ITEM_PUMPKIN = "pumpkin"
ITEM_APPLE = "apple"
ITEM_CARRIAGE = "carriage"

# char names
CHAR_CINDERELLA = "Cinderella"
CHAR_SNOW_WHITE = "Snow White"
CHAR_EVIL_QUEEN = "Evil Queen"
CHAR_BEAR = "Bear"

# state flags
STATE_HAS_MAP = "has_map"
STATE_HAS_LIGHTSABER = "has_lightsaber"
STATE_HAS_HELPED_BEAR = "has_helped_bear"
STATE_BEAR_ALLOWED_PASSAGE = "bear_allowed_passage"
STATE_QUEEN_DEFEATED = "queen_defeated"
STATE_SNOW_WHITE_RESCUED = "snow_white_rescued"
STATE_ATE_APPLE = "ate_apple"
STATE_HAS_CARRIAGE = "has_carriage"


@dataclass
class GameState:
    current_scene: str = SCENE_START
    inventory: List[str] = field(default_factory=list)
    health: int = 100
    flags: Dict[str, bool] = field(default_factory=dict)

    # for AI-generated temporary scenes
    pending_return_scene: Optional[str] = None
    dynamic_scene_data: Optional[Dict[str, Any]] = None


def create_new_game():
    return GameState(
        current_scene=SCENE_START,
        inventory=[],
        health=100,
        flags={
            STATE_HAS_MAP: False,
            STATE_HAS_LIGHTSABER: False,
            STATE_HAS_HELPED_BEAR: False,
            STATE_BEAR_ALLOWED_PASSAGE: False,
            STATE_QUEEN_DEFEATED: False,
            STATE_SNOW_WHITE_RESCUED: False,
            STATE_ATE_APPLE: False,
            STATE_HAS_CARRIAGE: False,
        },
        pending_return_scene=None,
        dynamic_scene_data=None,
    )


def add_item(state, item):
    if item not in state.inventory:
        state.inventory.append(item)


def remove_item(state, item):
    if item in state.inventory:
        state.inventory.remove(item)
        return True
    return False


def has_item(state, item):
    return item in state.inventory


def set_flag(state, flag_name, value=True):
    state.flags[flag_name] = value


def get_flag(state, flag_name):
    return state.flags.get(flag_name, False)


def transform_item(state, old_item, new_item, flag_name=None):
    if old_item in state.inventory:
        state.inventory.remove(old_item)
        if new_item not in state.inventory:
            state.inventory.append(new_item)
        if flag_name:
            state.flags[flag_name] = True
        return True
    return False


def clear_dynamic_scene(state):
    state.dynamic_scene_data = None
    state.pending_return_scene = None