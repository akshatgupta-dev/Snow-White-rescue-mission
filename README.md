# Snow-White-rescue-mission
Tkinter GUI text-adventure game in Python: Cinderella with a lightsaber rescues Snow White (save/load + inventory + puzzles)




# Shared Game Foundation

`game_foundation.py` is the shared base file for our group project.

Its purpose is to make sure everyone uses the same:
- scene names
- item names
- character names
- state flags
- game state structure

This file does **not** contain the full game.  
It only gives the basic structure that all group members will use when writing their own part.

## What it includes

- shared constants
- `GameState` class
- `create_new_game()` function
- helper functions:
  - `add_item()`
  - `has_item()`
  - `set_flag()`
  - `get_flag()`

## How to use it

Each group member should import from `game_foundation.py` in their own file.

Example:

```python
from game_foundation import *

def library_scene(state):
    pass