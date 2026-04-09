from src.game_foundation import (
    GameState,
    create_new_game,
    has_item,
    get_flag,
    SCENE_START,
    SCENE_LIBRARY,
    SCENE_AGORA,
    SCENE_CAFETERIA,
    SCENE_BEAR_BRIDGE,
    SCENE_KIRJURINLUOTO,
    SCENE_FINAL,
    DYNAMIC_SCENE,
    ITEM_LIGHTSABER,
    STATE_HAS_MAP,
    STATE_BEAR_ALLOWED_PASSAGE,
    STATE_SNOW_WHITE_RESCUED,
)

from pipeline.agora_scene import AgoraHallScene
from pipeline.akshat import play_kirjurinluoto_scene
from pipeline.scene1 import library_scene
from pipeline.cafeteria_v2 import play_cafeteria_scene
from pipeline.bear_bridge_v2 import play_bear_bridge_scene

from src.narrator import generate_story_block, print_block
from src.dynamic_scene import queue_dynamic_scene, play_dynamic_scene


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

    block = generate_story_block(
        "opening cutscene",
        state,
        "Cinderella is about to begin the journey toward the library."
    )
    print_block(block)

    input("\nPress Enter to begin the journey...")
    state.current_scene = SCENE_LIBRARY


def play_library_wrapper(state: GameState):
    state.current_scene = SCENE_LIBRARY

    intro = generate_story_block(
        "scene intro",
        state,
        "Cinderella is about to face the library guardian."
    )
    print_block(intro)

    while state.health > 0 and not get_flag(state, STATE_HAS_MAP):
        library_scene(state)

    if state.health <= 0:
        return

    if get_flag(state, STATE_HAS_MAP):
        outro = generate_story_block(
            "transition cutscene",
            state,
            "Cinderella has earned the map and is leaving for Agora Hall."
        )
        print_block(outro)

        queue_dynamic_scene(
            state,
            return_scene=SCENE_AGORA,
            extra_context="Cinderella has just earned the map and is walking from the library toward Agora Hall."
        )


def play_agora_wrapper(state: GameState, agora_scene: AgoraHallScene):
    state.current_scene = SCENE_AGORA

    intro = generate_story_block(
        "scene intro",
        state,
        "Cinderella enters Agora Hall and senses something important is hidden here."
    )
    print_block(intro)

    print("\n" + agora_scene.enter(state))

    while state.health > 0:
        if has_item(state, ITEM_LIGHTSABER):
            outro = generate_story_block(
                "transition cutscene",
                state,
                "Cinderella now has the lightsaber and is heading toward the cafeteria."
            )
            print_block(outro)

            print("\nCinderella leaves Agora Hall with the lightsaber.")
            queue_dynamic_scene(
                state,
                return_scene=SCENE_CAFETERIA,
                extra_context="Cinderella has won the lightsaber and is on the way from Agora Hall to the cafeteria."
            )
            return

        print("\nChoices:")
        for option in agora_scene.get_choices(state):
            print(option)

        choice = input("> ").strip()
        result = agora_scene.handle_choice(state, choice)
        print("\n" + result)

        if has_item(state, ITEM_LIGHTSABER):
            outro = generate_story_block(
                "transition cutscene",
                state,
                "With the weapon secured, the next part of the journey begins."
            )
            print_block(outro)

            print("\nWith the weapon secured, the path forward opens.")
            queue_dynamic_scene(
                state,
                return_scene=SCENE_CAFETERIA,
                extra_context="Cinderella has secured the lightsaber and is heading toward the cafeteria."
            )
            return


def play_cafeteria_wrapper(state: GameState):
    state.current_scene = SCENE_CAFETERIA

    intro = generate_story_block(
        "scene intro",
        state,
        "Cinderella arrives at the cafeteria before the next challenge."
    )
    print_block(intro)

    play_cafeteria_scene(state)

    if state.health <= 0:
        return

    if state.current_scene == SCENE_BEAR_BRIDGE:
        outro = generate_story_block(
            "transition cutscene",
            state,
            "The cafeteria scene is over and Cinderella pushes onward."
        )
        print_block(outro)

        queue_dynamic_scene(
            state,
            return_scene=SCENE_BEAR_BRIDGE,
            extra_context="Cinderella has just left the cafeteria in a magical carriage and is heading toward Bear Bridge."
        )


def play_bear_bridge_wrapper(state: GameState):
    state.current_scene = SCENE_BEAR_BRIDGE

    intro = generate_story_block(
        "scene intro",
        state,
        "Cinderella approaches the bridge where the bear blocks the way."
    )
    print_block(intro)

    play_bear_bridge_scene(state)

    if state.health <= 0:
        return

    if state.current_scene == SCENE_KIRJURINLUOTO:
        queue_dynamic_scene(
            state,
            return_scene=SCENE_KIRJURINLUOTO,
            extra_context="Cinderella has helped the bear and is now crossing toward Kirjurinluoto for the final confrontation."
        )


def play_kirjurinluoto_wrapper(state: GameState):
    state.current_scene = SCENE_KIRJURINLUOTO

    intro = generate_story_block(
        "scene intro",
        state,
        "Cinderella reaches the final area and prepares for the confrontation."
    )
    print_block(intro)

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

        elif state.current_scene == DYNAMIC_SCENE:
            play_dynamic_scene(state)

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