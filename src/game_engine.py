"""
Game engine: orchestrates scene flow and state management.

Does NOT call input() directly. Instead, uses input_manager to intercept
input() calls from scene functions and provide queued input.

Pure engine: given a GameState and a scene to play, it executes that scene
and returns the updated state + a status (whether to continue, win, or lose).
"""

import queue
from src.game_foundation import (
    GameState,
    create_new_game,
    get_flag,
    SCENE_START,
    SCENE_LIBRARY,
    SCENE_AGORA,
    SCENE_CAFETERIA,
    SCENE_BEAR_BRIDGE,
    SCENE_KIRJURINLUOTO,
    SCENE_FINAL,
    STATE_SNOW_WHITE_RESCUED,
)
from src.input_manager import set_input_source, clear_input_source, activate_queue_input, deactivate_queue_input
from pipeline.agora_scene import AgoraHallScene
from pipeline.scene1 import library_scene
from pipeline.akshat import play_kirjurinluoto_scene
from pipeline.cafeteria_v2 import play_cafeteria_scene
from pipeline.bear_bridge_v2 import play_bear_bridge_scene


class GameEngine:
    """Orchestrates game flow and scene management."""

    def __init__(self):
        self.state = None
        self.agora_scene_instance = AgoraHallScene()
        self.input_queue = None
        self.is_running = False

    def new_game(self):
        """Initialize a new game."""
        self.state = create_new_game()
        self.is_running = True
        return self.state

    def load_game(self, state):
        """Load a saved game state."""
        # TODO: implement deserialization later
        self.state = state
        self.is_running = True
        return self.state

    def set_input_queue(self, q):
        """Inject the input queue (from UI layer)."""
        self.input_queue = q
        set_input_source(q)
        activate_queue_input()

    def clear_input_queue(self):
        """Remove the input queue and restore stdlib input()."""
        deactivate_queue_input()
        clear_input_source()
        self.input_queue = None

    def play_scene(self):
        """
        Execute the current scene.
        Returns (status, message).
        Status: 'continue', 'win', 'lose', 'unknown_scene'
        """
        if self.state.health <= 0:
            return "lose", "Cinderella's health reached 0."

        if get_flag(self.state, STATE_SNOW_WHITE_RESCUED):
            return "win", "Snow White has been rescued!"

        scene = self.state.current_scene

        try:
            if scene == SCENE_START:
                self._play_start_scene()
                return "continue", ""

            elif scene == SCENE_LIBRARY:
                library_scene(self.state)
                if self.state.health <= 0:
                    return "lose", "Cinderella's health reached 0."
                return "continue", ""

            elif scene == SCENE_AGORA:
                self._play_agora_scene()
                if self.state.health <= 0:
                    return "lose", "Cinderella's health reached 0."
                return "continue", ""

            elif scene == SCENE_CAFETERIA:
                play_cafeteria_scene(self.state)
                if self.state.health <= 0:
                    return "lose", "Cinderella's health reached 0."
                return "continue", ""

            elif scene == SCENE_BEAR_BRIDGE:
                play_bear_bridge_scene(self.state)
                if self.state.health <= 0:
                    return "lose", "Cinderella's health reached 0."
                return "continue", ""

            elif scene == SCENE_KIRJURINLUOTO:
                if not self.state.flags.get("bear_allowed_passage", False):
                    # Redirect back to bear bridge
                    self.state.current_scene = SCENE_BEAR_BRIDGE
                    return "continue", ""
                play_kirjurinluoto_scene(self.state)
                if self.state.health <= 0:
                    return "lose", "Cinderella's health reached 0."
                return "continue", ""

            elif scene == SCENE_FINAL:
                return "win", "Snow White has been rescued!"

            else:
                return "unknown_scene", f"Unknown scene: {scene}"

        except Exception as e:
            return "error", f"Scene error: {str(e)}"

    def _play_start_scene(self):
        """Intro scene."""
        self.state.current_scene = SCENE_START
        print("\n" + "=" * 50)
        print("FAIRYTALE ADVENTURE: CINDERELLA IN PORI")
        print("=" * 50)
        print("\nCinderella wakes up in a strange magical version of SAMK.")
        print("She must cross the campus, defeat the Evil Queen,")
        print("and rescue Snow White.")
        print("\nPress Enter to begin the journey...\n")
        input()
        self.state.current_scene = SCENE_LIBRARY

    def _play_agora_scene(self):
        """Agora scene with choice handling."""
        print("\n" + self.agora_scene_instance.enter(self.state))

        while self.state.health > 0:
            from src.game_foundation import has_item, ITEM_LIGHTSABER

            if has_item(self.state, ITEM_LIGHTSABER):
                print("\nCinderella leaves Agora Hall with the lightsaber.")
                self.state.current_scene = SCENE_CAFETERIA
                return

            print("\nChoices:")
            for option in self.agora_scene_instance.get_choices(self.state):
                print(option)

            choice = input("> ").strip()
            result = self.agora_scene_instance.handle_choice(self.state, choice)
            print("\n" + result)

            if has_item(self.state, ITEM_LIGHTSABER):
                print("\nWith the weapon secured, Cinderella moves forward.")
                self.state.current_scene = SCENE_CAFETERIA
                return

    def save_game(self, filepath="savegame.json"):
        """Save current game state to JSON."""
        # TODO: implement serialization
        pass

    def load_game_from_file(self, filepath="savegame.json"):
        """Load game state from JSON."""
        # TODO: implement deserialization
        pass
