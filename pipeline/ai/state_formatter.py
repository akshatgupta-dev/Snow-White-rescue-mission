from game_foundation import GameState


def format_inventory(state: GameState) -> str:
    if not state.inventory:
        return "none"
    return ", ".join(state.inventory)


def format_active_flags(state: GameState) -> str:
    active_flags = [flag for flag, value in state.flags.items() if value]

    if not active_flags:
        return "none"

    return ", ".join(active_flags)


def format_state_summary(state: GameState) -> str:
    return (
        f"Current scene: {state.current_scene}\n"
        f"Health: {state.health}\n"
        f"Inventory: {format_inventory(state)}\n"
        f"Active flags: {format_active_flags(state)}"
    )