from dataclasses import dataclass, field
from typing import List, Dict

# scene names
SCENE_START = "start"
SCENE_LIBRARY = "library"
SCENE_AGORA = "agora_hall"
SCENE_CAFETERIA = "cafeteria"
SCENE_BEAR_BRIDGE = "bear_bridge"
SCENE_KIRJUONLUONTO = "kirjuonluonto"
SCENE_FINAL = "final"


# item names
ITEM_MAP = "map"
ITEM_LIGHTSABER = "lightsaber"
ITEM_PUMPKIN = "pumpkin"
ITEM_APPLE = "apple"



# char names
CHAR_CINDERELLA = "Cinderella"
CHAR_SNOW_WHITE = "Snoe White"
CHAR_EVIL_QUEEN = "Evil Queen"
CHAR_BEAR = "Bear"

# state flags
STATE_HAS_MAP = "has_map"
STATE_HAS_LIGHTSABER= "has_lightsaber"
STATE_HAS_HELPED_BEAR = "has_helped_bear"

STATE_BEAR_ALLOWED_PASSAGE  = "bear_allowed_passage"
STATE_QUEEN_DEFEATED = "queen_defeated"
STATE_SNOW_WHITE_RESCUED = "snow_white_rescued"
STATE_ATE_APPLE = "ate_apple"


@dataclass
class GameState:
    current_scene: str = SCENE_START #creates var in class which has to be a str
    inventory: List[str] = field(default_factory=list) #stores a list of strings
    
    health:int =100 #player health starts at 100
    flags:Dict[str, bool] = field(default_factory=dict)
    
    
def create_new_game():
    return GameState( #creates a strting game and give it
        current_scene=SCENE_START, 
        inventory=[], #0 inventory at the start
        health=100, #100 health at the start
        flags={
            STATE_HAS_MAP:False, 
            STATE_HAS_LIGHTSABER:False,
            STATE_HAS_HELPED_BEAR:False,
            STATE_BEAR_ALLOWED_PASSAGE: False,
            STATE_QUEEN_DEFEATED: False,
            STATE_SNOW_WHITE_RESCUED: False,
            STATE_ATE_APPLE: False,
        } # at the sart the player has not accomplished anything so everything is set to false
    )
    
def add_item(state, item): # adding items into the inventory
    if item not in state.inventory:
        state.inventory.append(item)
        
def has_item(state, item): # seeing what items are in the inventory
    return item in state.inventory


def set_flag(state, flag_name, value=True): # for changing flag value
    state.flags[flag_name] = value
    
def get_flag(state, flag_name): #read flag value
    return state.flags.get(flag_name, False)