"""
Game engine: orchestrates scene flow and state management.

Adapted for UI implementations (like Tkinter) to seamlessly wrap 
the shared core logic found in pipeline.runner.
"""

from pipeline.runner import start_game, get_scene_packet, apply_action

class GameEngine:
    """Orchestrates game flow and scene management by wrapping the pipeline runner."""

    def __init__(self):
        self.state = None
        self.shown_intro_scenes = set()
        self.last_packet = None

    def new_game(self):
        """Initialize a new game."""
        self.state, self.shown_intro_scenes = start_game()
        self.last_packet = get_scene_packet(self.state, self.shown_intro_scenes)
        return self.last_packet

    def submit_choice(self, action_index, user_input=None):
        """Submit a user choice to the engine and return the updated scene packet."""
        self.last_packet = apply_action(
            self.state,
            self.shown_intro_scenes,
            action_index,
            user_input=user_input,
        )
        return self.last_packet

    def load_game(self, state):
        """Load a saved game state."""
        # TODO: implement deserialization later
        self.state = state
        self.shown_intro_scenes = set()
        self.last_packet = get_scene_packet(self.state, self.shown_intro_scenes)
        return self.last_packet

    def save_game(self, filepath="savegame.json"):
        """Save current game state to JSON."""
        # TODO: implement serialization
        pass

    def load_game_from_file(self, filepath="savegame.json"):
        """Load game state from JSON."""
        # TODO: implement deserialization
        pass