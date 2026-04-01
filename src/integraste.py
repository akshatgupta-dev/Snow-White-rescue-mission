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
    print("\n" + agora_scene.enter(state))

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