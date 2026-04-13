from pipeline.game_foundation import (
    create_new_game,
    SCENE_LIBRARY,
    SCENE_AGORA,
    SCENE_CAFETERIA,
    SCENE_BEAR_BRIDGE,
    SCENE_KIRJURINLUOTO,
    SCENE_FINAL,
)

from pipeline.ai.narrator import generate_narration

from pipeline.scenes.library_scene import (
    get_library_intro,
    get_library_actions,
    handle_library_action,
)
from pipeline.scenes.agora_scene import (
    get_agora_intro,
    get_agora_actions,
    handle_agora_action,
)
from pipeline.scenes.cafeteria_scene import (
    get_cafeteria_intro,
    get_cafeteria_actions,
    handle_cafeteria_action,
)
from pipeline.scenes.bear_bridge_scene import (
    get_bear_bridge_intro,
    get_bear_bridge_actions,
    handle_bear_bridge_action,
)
from pipeline.scenes.kirjurinluoto_sccene import (
    get_kirjurinluoto_intro,
    get_kirjurinluoto_actions,
    handle_kirjurinluoto_action,
)
from pipeline.scenes.final_scene import (
    get_final_intro,
    get_final_actions,
    handle_final_action,
)


SCENE_REGISTRY = {
    SCENE_LIBRARY: {
        "intro": get_library_intro,
        "actions": get_library_actions,
        "handler": handle_library_action,
    },
    SCENE_AGORA: {
        "intro": get_agora_intro,
        "actions": get_agora_actions,
        "handler": handle_agora_action,
    },
    SCENE_CAFETERIA: {
        "intro": get_cafeteria_intro,
        "actions": get_cafeteria_actions,
        "handler": handle_cafeteria_action,
    },
    SCENE_BEAR_BRIDGE: {
        "intro": get_bear_bridge_intro,
        "actions": get_bear_bridge_actions,
        "handler": handle_bear_bridge_action,
    },
    SCENE_KIRJURINLUOTO: {
        "intro": get_kirjurinluoto_intro,
        "actions": get_kirjurinluoto_actions,
        "handler": handle_kirjurinluoto_action,
    },
    SCENE_FINAL: {
        "intro": get_final_intro,
        "actions": get_final_actions,
        "handler": handle_final_action,
    },
}


def print_status(state):
    print("\n" + "-" * 40)
    print(f"Scene: {state.current_scene}")
    print(f"Health: {state.health}")
    print(f"Inventory: {', '.join(state.inventory) if state.inventory else 'empty'}")
    print("-" * 40)


def narrate_result(state, result, player_action=""):
    narration = generate_narration(
        state=state,
        prompt_type=result["prompt_type"],
        scene_id=result["scene_id"],
        scene_facts=result["scene_facts"],
        player_action=player_action,
    )
    print("\n" + narration + "\n")


def choose_action(actions):
    print("Actions:")
    for index, action in enumerate(actions, start=1):
        print(f"{index}. {action['label']}")

    while True:
        choice = input("\nChoose an action number: ").strip()

        if not choice.isdigit():
            print("Please enter a valid number.")
            continue

        choice_num = int(choice)
        if 1 <= choice_num <= len(actions):
            return actions[choice_num - 1]

        print("That number is not one of the available actions.")


def collect_action_input(action):
    if not action.get("input_required", False):
        return None

    hint = action.get("input_hint", "Enter input:")
    return input(f"{hint}\n> ").strip()


def get_scene_intro(scene_id, state):
    intro_fn = SCENE_REGISTRY[scene_id]["intro"]

    if scene_id == SCENE_BEAR_BRIDGE:
        return intro_fn(state)

    return intro_fn()


def main():
    state = create_new_game()
    state.current_scene = SCENE_LIBRARY

    shown_intro_scenes = set()

    while True:
        if state.health <= 0:
            print("\nGAME OVER")
            break

        print_status(state)

        scene_id = state.current_scene
        scene_config = SCENE_REGISTRY.get(scene_id)

        if scene_config is None:
            print(f"\nUnknown scene: {scene_id}")
            break

        if scene_id not in shown_intro_scenes:
            intro_result = get_scene_intro(scene_id, state)
            narrate_result(state, intro_result)
            shown_intro_scenes.add(scene_id)

        actions = scene_config["actions"](state)
        chosen_action = choose_action(actions)
        user_input = collect_action_input(chosen_action)

        result = scene_config["handler"](
            state,
            chosen_action["action_id"],
            user_input,
        )

        narrate_result(state, result, player_action=chosen_action["label"])

        if result.get("game_over"):
            print("GAME OVER")
            break

        if result.get("game_complete"):
            print("YOU WIN!")
            break

        next_scene = result.get("next_scene")
        if next_scene:
            state.current_scene = next_scene
            continue

    print("\n" + "=" * 40)
    if state.health <= 0:
        print("GAME OVER")
    elif result.get("game_complete"):
        print("Snow White has been rescued.")
    else:
        print("GAME ENDED")
    print("=" * 40)


if __name__ == "__main__":
    main()