# Cinderella Rescues Snow White using her Lightsaber - Group Design Document

**Team Members:** Le Viet Lan Chi, Akshat Gupta, Trinh Kha, Rohit Gadgil  
**Date:** 5.02.2026  
**Version:** 1.0

---

## 1. Project Overview
We are building a menu-based Python text adventure game where the player controls Cinderella (with a lightsaber) on a mission to rescue Snow White. The player explores locations, collects items, unlocks paths, and makes choices that affect the outcome. It is meant for casual story gamers who hate any sort of visuals whatsoever and love terminal based games.

## 2. Goals & Objectives

* **Core Goal:** Create a complete playable text adventure with exploration, item collection, locked paths, and a clear win condition (rescue Snow White).
* **Secondary Goal:** Implement a Tkinter GUI and a save/load system (JSON) that stores both player and world state.

The program is “finished” when it:
Launches a GUI window with story output and controls
Supports New Game / Load Game / Save / Help / Quit
Displays the current location, description, items, exits, and player health
Allows actions via GUI:
Move (direction selector + Go)
Take item (room item selector + Take)
Use item (inventory selector + Use)
Special Action (context-based events like a puzzle or rescue trigger)
Uses locked paths that require specific items/actions to progress
Has at least one win ending (Snow White rescued) and one lose condition (health reaches 0)
Stores progress in savegame.json and can correctly restore it

## 3. The User Journey
*How will a person interact with our code?*
* **The Experience:** 

User runs the program and a Tkinter window opens.
User clicks New Game (or Load Game).
The story log shows the current location name, description, exits, and items.
User interacts with dropdowns and buttons to:
Move to new locations
Take items
Use items
Trigger special events/puzzles
The user reaches the tower, defeats the Evil Queen, and rescues Snow White (win), or loses health to traps/events (lose).
User can save anytime and reload later.

* **Inputs:** 

GUI buttons and dropdown choices (no text commands required)
Occasional pop-up inputs via GUI for puzzle answers (integer input dialog)

## 4. Program Logic (Step-by-Step)

1. **Initialization:** 

Import: tkinter, json, dataclasses, pathlib, typing

Define save path: savegame.json

Build world structure using build_world()

2. **GUI Startup**

Create main window with:
-Story log (scrollable text area)
-Status area (location, health, inventory)
-Buttons: New Game, Load Game, Save, Help, Quit
-Controls:
--Move dropdown + Go
--Room Items dropdown + Take Item
--Inventory dropdown + Use Item
--Special Action button

3. **New Game**

Prompt for player name (optional)
Create Player dataclass and initialize world dict
Render initial room view in the log

4. **Load Game**

Read JSON file into Player + world dict
Update GUI and render current room

5. **Gameplay (Event-Driven, Button-Based)**

Move button:
-Validate exit and check locked rules
-Move player, trigger entry events, update display
Take item button:
-Removes item from room list and adds to inventory
-Updates GUI dropdowns and status
Use item button:
-Applies item effect (unlock gate, disable lock, defeat Queen, etc.)
-Updates flags and state
Special Action:
-Runs context-based logic:
--Example: bridge puzzle (input dialog)
--Example: tower rescue event
--Example: queen chamber trap decision popup

6. **Win/Lose Checks**

Lose if health ≤ 0 → show “Game Over”
Win when Snow White rescued → show “Victory” popup

7. **Save / Quit**

Save writes {player, world} to savegame.json
Quit closes window safely

## 5. Team Responsibility Breakdown
*How are we dividing the work? Each member should have a primary area of focus.*
* **Le Viet Lan Chi:** Story Content & World Design 
* **Akshat Gupta:** GUI Framework & Integration
* **Trinh Kha:** Game Logic & Event System
* **Rohit Gadgil:** Save/Load, Data Integrity & Testing

## 6. Module & Function Breakdown
World/Data
-build_world() [Chi]
-pretty_item(item_id) [Chi]

Player State
-Player dataclass [Akshat + Kha]

Storage
-save_game(player, world) [Rohit]
-load_game() [Rohit]

Logic / Engine
-can_move(player, world, direction) [Kha]
-move_player(player, world, direction) [Kha]
-take_item(player, world, item) [Kha or Akshat—final integration decides]
-use_item(player, world, item) [Kha]
-apply_location_events(player, world) [Kha]
-special_action(player, world) [Kha]

GUI Layer
-GameApp class (Tkinter):
--new_game(), load_game(), save_game(), show_help(), quit_game() [Akshat]
--do_move(), do_take_item(), do_use_item(), do_special() [Akshat integrating logic from Kha]
--append_log(), update_menus(), render_room() [Akshat]

## 7. Data Storage & Structures
Player State
-location: str (current room ID)
-health: int
-inventory: List[str]
-flags: Dict[str, bool] (progress + event booleans)

World State
-Dictionary of rooms:
--name, desc
--exits: {direction: room_id}
--items: [item_id]
--locked_exits: {direction: lock_id}
--events: {visited: bool, special_flags...}

Persistence
-File: savegame.json
-Stores:
--player state (dataclass → dict)
--world dict (including items left + event states)

## 8. Development Timeline (Milestones)
*What is our plan for finishing on time?*
1. **Milestone 1:** [Week 1] - We will have the basic project structure and main menu working.
2. **Milestone 2:** [Week 2] - We will have our individual modules connected and talking to each other.
3. **Milestone 3:** [Week 3] - We will finish testing for bugs and submit the final version.

---

### Team Checklist:
* **Consistency:** Are we all using the same variable naming style (e.g., `snake_case`)?
We will all use the same variable naming style, first_word.
* **Communication:** How will we communicate? 
We will be using WhatsApp as our main communication mode in this project
* **Integration:** Have we tested if Member A's function actually works with Member B's function?
Akshat will test integration after any significant commit.