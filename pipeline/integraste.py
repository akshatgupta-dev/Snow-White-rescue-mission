from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def load_module(module_name: str, candidate_files: list[str]):
    """Load a module from the first matching filename in this folder."""
    for filename in candidate_files:
        path = BASE_DIR / filename
        if path.exists():
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {filename}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module

    raise FileNotFoundError(
        f"Could not find any of these files for {module_name}: {candidate_files}"
    )


foundation = load_module("foundation", ["foundation.py", "game_foundation.py"])
sys.modules["game_foundation"] = foundation

pipeline_pkg = types.ModuleType("pipeline")
pipeline_pkg.game_foundation = foundation
sys.modules["pipeline"] = pipeline_pkg
sys.modules["pipeline.game_foundation"] = foundation

member1 = load_module("member1", ["akshat.py"])
member2 = load_module("member2", ["agora_scene.py"])
bear_bridge_mod = load_module("bear_bridge", ["bear_bridge_v2.py"])
cafeteria_mod = load_module("cafeteria", ["cafeteria_v2.py"])
member4 = load_module("member4", ["scene1.py"])


# Pull required names from foundation
GameState = foundation.GameState
create_new_game = foundation.create_new_game
has_item = foundation.has_item
get_flag = foundation.get_flag

SCENE_START = foundation.SCENE_START
SCENE_LIBRARY = foundation.SCENE_LIBRARY
SCENE_AGORA = foundation.SCENE_AGORA
SCENE_CAFETERIA = foundation.SCENE_CAFETERIA
SCENE_BEAR_BRIDGE = foundation.SCENE_BEAR_BRIDGE
SCENE_KIRJURINLUOTO = foundation.SCENE_KIRJURINLUOTO
SCENE_FINAL = foundation.SCENE_FINAL

ITEM_LIGHTSABER = foundation.ITEM_LIGHTSABER

STATE_HAS_MAP = foundation.STATE_HAS_MAP
STATE_BEAR_ALLOWED_PASSAGE = foundation.STATE_BEAR_ALLOWED_PASSAGE
STATE_SNOW_WHITE_RESCUED = foundation.STATE_SNOW_WHITE_RESCUED

AgoraHallScene = member2.AgoraHallScene
play_kirjurinluoto_scene = member1.play_kirjurinluoto_scene
play_cafeteria_scene = cafeteria_mod.play_cafeteria_scene
play_bear_bridge_scene = bear_bridge_mod.play_bear_bridge_scene
library_scene = member4.library_scene


def print_status(state: GameState):
    print("\n" + "-" * 40)
    print(f"Scene: {state.current_scene}")
    print(f"Health: {state.health}")
    print(f"Inventory: {', '.join(state.inventory) if state.inventory else 'empty'}")
    print("-" * 40)


def play_start_scene(state: GameState):
    state.current_scene = SCENE_START
    print("\n" + "=" * 40)
    print("FAIRYTALE ADVENTURE: CINDERELLA IN PORI")
    print("=" * 40)
    print("Cinderella wakes up in a strange magical version of SAMK.")
    print("She must cross the campus, defeat the Evil Queen,")
    print("and rescue Snow White.")
    input("\nPress Enter to begin the journey...")
    state.current_scene = SCENE_LIBRARY


def play_library_wrapper(state: GameState):
    state.current_scene = SCENE_LIBRARY

    while state.health > 0 and not get_flag(state, STATE_HAS_MAP):
        library_scene(state)

        if state.health <= 0:
            print("\nCinderella can no longer continue.")
            return

        if get_flag(state, STATE_HAS_MAP):
            print("\nCinderella uses the glowing map and moves on.")
            return

        print("\nThe guardian still blocks the way. Try again.")


def play_agora_wrapper(state: GameState, agora_scene: AgoraHallScene):
    first_entry_text = agora_scene.enter(state)
    print("\n" + first_entry_text)

    while state.health > 0:
        if has_item(state, ITEM_LIGHTSABER):
            print("\nCinderella leaves Agora Hall with the lightsaber.")
            state.current_scene = SCENE_CAFETERIA
            return

        print("\nChoices:")
        for option in agora_scene.get_choices(state):
            print(option)

        choice = input("> ").strip()
        result = agora_scene.handle_choice(state, choice)
        print("\n" + result)

        if has_item(state, ITEM_LIGHTSABER):
            print("\nWith the weapon secured, the path forward opens.")
            state.current_scene = SCENE_CAFETERIA
            return


def play_cafeteria_wrapper(state: GameState):
    state.current_scene = SCENE_CAFETERIA
    play_cafeteria_scene(state)


def play_bear_bridge_wrapper(state: GameState):
    state.current_scene = SCENE_BEAR_BRIDGE
    play_bear_bridge_scene(state)


def play_kirjurinluoto_wrapper(state: GameState):
    state.current_scene = SCENE_KIRJURINLUOTO
    play_kirjurinluoto_scene(state)


def main():
    state = create_new_game()
    agora_scene = AgoraHallScene()

    while state.health > 0:
        print_status(state)

        if state.current_scene == SCENE_START:
            play_start_scene(state)

        elif state.current_scene == SCENE_LIBRARY:
            play_library_wrapper(state)

        elif state.current_scene == SCENE_AGORA:
            play_agora_wrapper(state, agora_scene)

        elif state.current_scene == SCENE_CAFETERIA:
            play_cafeteria_wrapper(state)

        elif state.current_scene == SCENE_BEAR_BRIDGE:
            play_bear_bridge_wrapper(state)

        elif state.current_scene == SCENE_KIRJURINLUOTO:
            if not get_flag(state, STATE_BEAR_ALLOWED_PASSAGE):
                print("\nThe way is still blocked.")
                state.current_scene = SCENE_BEAR_BRIDGE
            else:
                play_kirjurinluoto_wrapper(state)

        elif state.current_scene == SCENE_FINAL:
            break

        else:
            print(f"\nUnknown scene: {state.current_scene}")
            break

        if get_flag(state, STATE_SNOW_WHITE_RESCUED):
            break

    print("\n" + "=" * 40)
    if state.health <= 0:
        print("GAME OVER")
    elif get_flag(state, STATE_SNOW_WHITE_RESCUED):
        print("YOU WIN!")
        print("Snow White has been rescued.")
    else:
        print("GAME ENDED")
    print("=" * 40)


if __name__ == "__main__":
    main()