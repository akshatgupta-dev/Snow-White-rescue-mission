"""Agora Hall scene module.

This class is intentionally focused on scene-local narrative and choices.
The main game runner can import this class and call its methods as part of
the full game flow.
"""

from pipeline.game_foundation import (
    SCENE_AGORA,
    ITEM_LIGHTSABER,
    has_item,
)


class AgoraHallScene:
    """Encapsulates the Agora Hall story segment and scene-local state."""

    def __init__(self):
        self._intro_shown = False
        self._challenge_started = False

    def enter(self, state):
        """Enter Agora Hall and return scene narrative text."""
        state.current_scene = SCENE_AGORA

        if self._intro_shown:
            return (
                "You step back into Agora Hall. The Seven Dwarfs are still in "
                "matching badminton outfits, guarding the lightsaber like this "
                "is the most normal thing in the world."
            )

        self._intro_shown = True
        return (
            "Cinderella follows the clue into Agora Hall. In the center of the "
            "room, the Seven Dwarfs stand shoulder to shoulder in matching "
            "badminton outfits. Behind them, on a display stand under harsh "
            "lights, rests a lightsaber.\n\n"
            "Doc steps forward and clears his throat. 'If you want the weapon, "
            "you play us for it. One badminton round. Win, and it's yours.'"
        )

    def get_choices(self, state):
        """Return player-facing actions currently available in Agora Hall."""
        if has_item(state, ITEM_LIGHTSABER):
            return [
                "1. Leave Agora Hall (you already claimed the lightsaber).",
            ]

        if self._challenge_started:
            return [
                "1. Continue to the badminton challenge.",
                "2. Take a breath and re-read the dwarfs' formation.",
            ]

        return [
            "1. Study the Seven Dwarfs and their formation.",
            "2. Ask why they are guarding a lightsaber.",
            "3. Accept the badminton challenge.",
        ]

    def handle_choice(self, state, choice):
        """Handle a scene choice and return narrative feedback.

        Note: full badminton challenge resolution is intentionally implemented
        in the next step.
        """
        if has_item(state, ITEM_LIGHTSABER):
            return (
                "You tighten your grip on the lightsaber and leave Agora Hall. "
                "There is nothing left to prove here."
            )

        if not self._challenge_started:
            if choice == "1":
                return (
                    "You observe their court position carefully. They're eager "
                    "and aggressive, crowding the front line whenever they "
                    "prepare to attack."
                )
            if choice == "2":
                return (
                    "Grumpy shrugs. 'No reason. Just vibes.' Doc rolls his eyes "
                    "and repeats the rule: win one round, win the lightsaber."
                )
            if choice == "3":
                self._challenge_started = True
                return (
                    "You spin the racket once and nod. The dwarfs cheer, rush to "
                    "their positions, and the badminton challenge begins."
                )
            return "Invalid choice. Pick 1, 2, or 3."

        if choice == "1":
            return (
                "You step onto the court. The round is ready to play. "
                "(Challenge resolution comes in the next implementation step.)"
            )
        if choice == "2":
            return (
                "You watch them again: all seven keep drifting to the front. "
                "There is always open space behind them."
            )
        return "Invalid choice. Pick 1 or 2."
