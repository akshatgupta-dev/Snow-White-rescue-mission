from pipeline.game_foundation import (
    SCENE_KIRJURINLUOTO,
    ITEM_PUMPKIN,
    ITEM_CARRIAGE,
    STATE_HAS_HELPED_BEAR,
    STATE_BEAR_ALLOWED_PASSAGE,
    has_item,
    remove_item,
    set_flag,
    transform_item,
)

def play_bear_bridge_scene(state):
    print("\n--- Bear Bridge ---")

    if has_item(state, ITEM_CARRIAGE):
        transform_item(state, ITEM_CARRIAGE, ITEM_PUMPKIN)
        print("The magical carriage suddenly turns back into an ordinary pumpkin.")

    print("Cinderella is about to eat the pumpkin when she hears crying nearby.")
    print("A hungry bear sits beside the bridge.")
    print("The bear looks too weak to guard the crossing properly.")

    print("\nChoices: give pumpkin, talk to bear, leave")

    choice = input("> ").strip().lower()

    if choice == "give pumpkin":
        if remove_item(state, ITEM_PUMPKIN):
            set_flag(state, STATE_HAS_HELPED_BEAR, True)
            set_flag(state, STATE_BEAR_ALLOWED_PASSAGE, True)
            print("Cinderella gives the pumpkin to the bear.")
            print("The bear happily eats it and smiles.")
            print("It reveals that it is the guardian of Pori and Kirjurinluoto.")
            print("Because Cinderella was kind, the bear allows her to pass.")
            state.current_scene = SCENE_KIRJURINLUOTO
        else:
            print("Cinderella has no pumpkin to give.")

    elif choice == "talk to bear":
        print('The bear sighs and says, "I am too hungry to guard this bridge."')

    elif choice == "leave":
        print("Cinderella steps away from the bridge for now.")

    else:
        print("Invalid choice.")