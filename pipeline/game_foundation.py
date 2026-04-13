from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional

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
CHAR_SEVEN_DWARFS ="Seven Dwarfs"

# state flags
STATE_HAS_MAP = "has_map"
STATE_HAS_LIGHTSABER= "has_lightsaber"
STATE_HAS_HELPED_BEAR = "has_helped_bear"

STATE_BEAR_ALLOWED_PASSAGE  = "bear_allowed_passage"
STATE_QUEEN_DEFEATED = "queen_defeated"
STATE_SNOW_WHITE_RESCUED = "snow_white_rescued"
STATE_ATE_APPLE = "ate_apple"

STATE_HAS_CARRIAGE = "has_carriage"


# state AGORA
STATE_AGORA_CHALLENGE_STARTED = "agora_challenge_started"
STATE_AGORA_RALLY_ACTIVE = "agora_rally_active"
STATE_AGORA_CHALLENGE_RESOLVED = "agora_challenge_resolved"
STATE_AGORA_CHALLENGE_WON = "agora_challenge_won"
STATE_AGORA_STUDIED_FORMATION = "agora_studied_formation"


@dataclass
class GameState:
    current_scene: str = SCENE_START
    inventory: List[str] = field(default_factory=list)
    pending_return_scene: Optional[str] = None
    dynamic_scene_data: Optional[Dict[str, Any]] = None
    health: int = 100
    flags: Dict[str, bool] = field(default_factory=dict)
    
    
def create_new_game():
    return GameState(
        current_scene=SCENE_START, 
        inventory=[], 
        pending_return_scene=None,
        dynamic_scene_data=None,
        health=100, 
        flags={
            # general states
            STATE_HAS_MAP: False, 
            STATE_HAS_LIGHTSABER: False,
            STATE_HAS_HELPED_BEAR: False,
            STATE_BEAR_ALLOWED_PASSAGE: False,
            STATE_QUEEN_DEFEATED: False,
            STATE_SNOW_WHITE_RESCUED: False,
            STATE_ATE_APPLE: False,
            STATE_HAS_CARRIAGE: False,

            # AGORA states
            STATE_AGORA_CHALLENGE_STARTED: False,
            STATE_AGORA_RALLY_ACTIVE: False,
            STATE_AGORA_CHALLENGE_RESOLVED: False,
            STATE_AGORA_CHALLENGE_WON: False,
            STATE_AGORA_STUDIED_FORMATION: False,
        }
    )

def clear_dynamic_scene(state: GameState):
    """Clears LLM-generated scene data and return pointers."""
    state.dynamic_scene_data = None
    state.pending_return_scene = None
    
def add_item(state: GameState, item: str) -> None:
    if item not in state.inventory:
        state.inventory.append(item)
        
def remove_item(state: GameState, item: str) -> bool:
    if item in state.inventory:
        state.inventory.remove(item)
        return True
    return False
        
def has_item(state: GameState, item: str) -> bool:
    return item in state.inventory

def set_flag(state: GameState, flag_name: str, value: bool = True) -> None:
    state.flags[flag_name] = value
    
def get_flag(state: GameState, flag_name: str) -> bool:
    return state.flags.get(flag_name, False)

def damage_player(state: GameState, amount: int) -> None:
    state.health = max(0, state.health - amount)

def heal_player(state: GameState, amount: int) -> None:
    state.health = min(100, state.health + amount)

def transform_item(
        state: GameState,
        old_item: str,
        new_item: str,
        flag_name: str | None = None,
) -> bool:
    if old_item not in state.inventory:
        return False

    state.inventory.remove(old_item)

    if new_item not in state.inventory:
        state.inventory.append(new_item)

    if flag_name is not None:
        state.flags[flag_name] = True

    return True