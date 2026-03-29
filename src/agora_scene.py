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
        self._in_rally = False
        self._challenge_resolved = False
        self._challenge_won = False

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

        if self._challenge_resolved:
            if self._challenge_won:
                return [
                    "1. Catch your breath after winning the rally.",
                    "2. Step toward the lightsaber stand.",
                ]
            return [
                "1. Try another rally.",
                "2. Re-read their formation before serving.",
            ]

        if self._in_rally:
            return [
                "1. Smash straight at the front line.",
                "2. Try a soft drop shot near the net.",
                "3. Send the shuttle behind all seven dwarfs.",
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
        """Handle a scene choice and return narrative feedback."""
        if has_item(state, ITEM_LIGHTSABER):
            return (
                "You tighten your grip on the lightsaber and leave Agora Hall. "
                "There is nothing left to prove here."
            )

        if self._challenge_resolved:
            if self._challenge_won:
                if choice == "1":
                    return (
                        "The dwarfs are still untangling from each other while "
                        "you try very hard not to laugh."
                    )
                if choice == "2":
                    return (
                        "You step toward the lightsaber stand while Doc exhales "
                        "in dramatic defeat."
                    )
                return "Invalid choice. Pick 1 or 2."

            if choice == "1":
                self._in_rally = True
                self._challenge_resolved = False
                return (
                    "You roll your shoulders and serve again. The seven dwarfs "
                    "rush forward as a unit, repeating the same risky formation."
                )
            if choice == "2":
                return (
                    "You watch their footwork: all seven commit to the front "
                    "court whenever the pace rises."
                )
            return "Invalid choice. Pick 1 or 2."

        if self._in_rally:
            return self._resolve_rally_choice(choice)

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
            self._in_rally = True
            return (
                "The rally starts fast. Every dwarf charges to the front at "
                "once, leaving the back court wide open. Choose your shot."
            )
        if choice == "2":
            return (
                "You watch them again: all seven keep drifting to the front. "
                "There is always open space behind them."
            )
        return "Invalid choice. Pick 1 or 2."

    def _resolve_rally_choice(self, choice):
        """Resolve one tactical choice during the badminton rally."""
        self._in_rally = False
        self._challenge_resolved = True

        if choice == "3":
            self._challenge_won = True
            return (
                "You flick the shuttle deep behind them. All seven dwarfs spin "
                "around at once, crash into each other, and collapse into a "
                "legendary pileup. The rally is yours."
            )

        self._challenge_won = False
        if choice == "1":
            return (
                "You smash straight into the crowded front line. Bashful blocks "
                "it by accident, and the shuttle drops on your side. You lose "
                "the rally."
            )
        if choice == "2":
            return (
                "You attempt a gentle drop, but with seven dwarfs camping the "
                "net, Sleepy taps it back lazily for the point. You lose the "
                "rally."
            )
        return "Invalid shot choice. Pick 1, 2, or 3."
