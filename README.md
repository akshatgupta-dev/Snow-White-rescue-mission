# Snow-White-rescue-mission
Tkinter GUI text-adventure game in Python: Cinderella with a lightsaber rescues Snow White (save/load + inventory + puzzles)

## Run

- GUI (preferred): `python3 main_ui.py`
- Force terminal mode: `UI_FORCE_CLI=1 python3 main_ui.py`

### WSL GUI troubleshooting

If the GUI does not open (or `tk.Tk()` hangs), it is usually a WSLg/Xwayland issue rather than the game code.

- From Windows PowerShell run: `wsl --shutdown`
- Reopen your distro, then try `python3 main_ui.py` again
- If it still fails: `wsl --update` (and reboot Windows if needed)

Notes:
- `wsl` is a Windows command; it will not work as-is inside Ubuntu.
- From inside WSL you can run the Windows CLI explicitly:
  - `/mnt/c/Windows/System32/wsl.exe --shutdown`
  - `/mnt/c/Windows/System32/wsl.exe --update`




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