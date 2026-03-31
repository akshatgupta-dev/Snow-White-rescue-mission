from pipeline.game_foundation import (
    SCENE_BEAR_BRIDGE,
    SCENE_CAFETERIA,
    ITEM_PUMPKIN,
    ITEM_CARRIAGE,
    STATE_HAS_CARRIAGE,
    add_item,
    has_item,
    transform_item,
)

def play_cafeteria_screne(state):
    print("\n--- SAMK Cafeteria ---")
    print("The cafeteria is quiet and dark.")
    print("On a table sits a beautiful pumpkin.")

    if not has_item(state, ITEM_PUMPKIN) and not has_item(state, ITEM_CARRIAGE):
        print("\nChoices: take pumpkin, leave")
    else:
        print("\nChoices: wait, leave")

    choice = input("> ").strip().lower()

    if choice == "take pumpkin":
        add_item(state, ITEM_PUMPKIN)
        print("Cinderella picks up the pumpkin.")
        print("The clock strikes 10:00 PM.")
        
        if transform_item(state, ITEM_PUMPKIN, ITEM_CARRIAGE, STATE_HAS_CARRIAGE):
            print("The pumpkin transforms into a magical carriage!")
            print('"…ok. Magic."')
            state.current_scene = SCENE_BEAR_BRIDGE

    elif choice == "wait":
        if has_item(state, ITEM_PUMPKIN):
            print("The clock strikes 10:00 PM.")
            
            if transform_item(state, ITEM_PUMPKIN, ITEM_CARRIAGE, STATE_HAS_CARRIAGE):
                print("The pumpkin transforms into a magical carriage!")
                print('"…ok. Magic."')
                state.current_scene = SCENE_BEAR_BRIDGE
        else:
            print("Nothing happens.")

    elif choice == "leave":
        print("Cinderella leaves the cafeteria.")

    else:
        print("Invalid choice.")