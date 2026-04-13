from pipeline.game_foundation import (
    create_new_game,
    SCENE_LIBRARY,
    SCENE_AGORA,
    SCENE_CAFETERIA,
    SCENE_BEAR_BRIDGE,
    SCENE_KIRJURINLUOTO,
    SCENE_FINAL,
    DYNAMIC_SCENE,
)

from pipeline.ai.narrator import generate_narration
from pipeline.ai.dynamic_scene import (
    queue_dynamic_scene,
    play_dynamic_scene,
    apply_dynamic_effect,
)

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
from pipeline.scenes.kirjurinluoto_scene import (
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


# ==========================================
# REUSABLE ENGINE FUNCTIONS
# ==========================================

def start_game():
    state = create_new_game()
    state.current_scene = SCENE_LIBRARY
    shown_intro_scenes = set()
    return state, shown_intro_scenes


def get_scene_packet(state, shown_intro_scenes):
    scene_id = state.current_scene
    
    packet = {
        "scene_id": scene_id,
        "health": state.health,
        "inventory": list(state.inventory),
        "intro_shown": scene_id in shown_intro_scenes,
        "narration": "",
        "actions": []
    }

    if scene_id == DYNAMIC_SCENE:
        dyn_data = play_dynamic_scene(state)
        packet["narration"] = dyn_data.get("narration", "")
        packet["actions"] = dyn_data.get("actions", [])
        packet["intro_shown"] = True
        return packet

    scene_config = SCENE_REGISTRY.get(scene_id)
    if not scene_config:
        return packet

    if not packet["intro_shown"]:
        intro_result = get_scene_intro(scene_id, state)
        packet["narration"] = generate_narration(
            state=state,
            prompt_type=intro_result["prompt_type"],
            scene_id=intro_result["scene_id"],
            scene_facts=intro_result["scene_facts"],
            player_action=""
        )
        shown_intro_scenes.add(scene_id)
        packet["intro_shown"] = True

    packet["actions"] = scene_config["actions"](state)
    return packet


def apply_action(state, shown_intro_scenes, action_index, user_input=None):
    scene_id = state.current_scene
    player_action_label = ""
    
    if scene_id == DYNAMIC_SCENE:
        dyn_data = play_dynamic_scene(state)
        if 0 <= action_index < len(dyn_data.get("actions", [])):
            player_action_label = dyn_data["actions"][action_index].get("label", "")
        result = apply_dynamic_effect(state, action_index, user_input)
    else:
        scene_config = SCENE_REGISTRY[scene_id]
        actions = scene_config["actions"](state)
        chosen_action = actions[action_index]
        player_action_label = chosen_action["label"]
        
        result = scene_config["handler"](
            state,
            chosen_action["action_id"],
            user_input
        )

    # Generate the action consequence narration
    if "prompt_type" in result:
        narration = generate_narration(
            state=state,
            prompt_type=result["prompt_type"],
            scene_id=result.get("scene_id", scene_id),
            scene_facts=result.get("scene_facts", ""),
            player_action=player_action_label,
        )
    else:
        narration = result.get("narration", "")

    # Handle transitions and inject dynamic scenes
    next_scene = result.get("next_scene")
    if next_scene:
        valid_dynamic_transitions = [
            (SCENE_LIBRARY, SCENE_AGORA),
            (SCENE_AGORA, SCENE_CAFETERIA),
            (SCENE_CAFETERIA, SCENE_BEAR_BRIDGE),
            (SCENE_BEAR_BRIDGE, SCENE_KIRJURINLUOTO)
        ]
        
        if (state.current_scene, next_scene) in valid_dynamic_transitions:
            queue_dynamic_scene(state, state.current_scene, next_scene)
            state.current_scene = DYNAMIC_SCENE
        else:
            state.current_scene = next_scene

    return {
        "narration": narration,
        "game_over": result.get("game_over", False),
        "game_complete": result.get("game_complete", False),
        "next_scene": state.current_scene,
        "health": state.health,
        "inventory": list(state.inventory)
    }


# ==========================================
# CLI MAIN LOOP
# ==========================================

def main():
    state, shown_intro_scenes = start_game()
    result_packet = {}

    while True:
        if state.health <= 0:
            print("\nGAME OVER")
            break

        print_status(state)

        # Get the current scene data (including intro narrations if newly visited)
        packet = get_scene_packet(state, shown_intro_scenes)

        if packet.get("narration"):
            print("\n" + packet["narration"] + "\n")

        actions = packet.get("actions", [])
        if not actions:
            print("\nNo available actions. You are stuck.")
            break

        # Process user choice
        chosen_action = choose_action(actions)
        action_index = actions.index(chosen_action)
        user_input = collect_action_input(chosen_action)

        # Apply choice to game engine
        result_packet = apply_action(state, shown_intro_scenes, action_index, user_input)

        if result_packet.get("narration"):
            print("\n" + result_packet["narration"] + "\n")

        if result_packet.get("game_over") or state.health <= 0:
            break

        if result_packet.get("game_complete"):
            break

    print("\n" + "=" * 40)
    if state.health <= 0 or result_packet.get("game_over"):
        print("GAME OVER")
    elif result_packet.get("game_complete"):
        print("Snow White has been rescued.")
    else:
        print("GAME ENDED")
    print("=" * 40)


if __name__ == "__main__":
    main()