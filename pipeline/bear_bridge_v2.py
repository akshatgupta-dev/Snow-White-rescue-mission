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
    print("The carriage rushes forward through the night...")

    # carriage turns back into pumpkin
    if has_item(state, ITEM_CARRIAGE):
        transform_item(state, ITEM_CARRIAGE, ITEM_PUMPKIN)
        print("Suddenly, the magic fades.")
        print("The carriage collapses back into a simple pumpkin.")
        print("Cinderella stares at it.")
        print('"…of course."')

    print("\nAs she approaches the bridge, she hears quiet sobbing.")
    print("A large bear sits by the side of the path, looking miserable.")

    while True:
        print("\nChoices: look around, talk to bear, give pumpkin, keep pumpkin")
        choice = input("> ").strip().lower()

        if choice == "look around":
            print("The bridge leads to Kirjurinluoto.")
            print("The forest beyond is covered in fog and strange magic.")
            print("The bear is clearly meant to guard the crossing... but it looks too weak.")

        elif choice == "talk to bear":
            print('The bear sighs deeply.')
            print('"I am supposed to guard this bridge..."')
            print('"But I am too hungry... I cannot even stand properly."')

        elif choice == "give pumpkin":
            if has_item(state, ITEM_PUMPKIN):
                remove_item(state, ITEM_PUMPKIN)
                set_flag(state, STATE_HAS_HELPED_BEAR, True)
                set_flag(state, STATE_BEAR_ALLOWED_PASSAGE, True)

                print("Cinderella looks at the pumpkin in her hands.")
                print("She sighs... and gives it to the bear.")
                print("\nThe bear immediately brightens and eats happily.")
                print('"Thank you," it says.')
                print('"I am the guardian of Pori... and of this bridge."')
                print("It steps aside and nods respectfully.")
                print("Cinderella may now pass.")

                state.current_scene = SCENE_KIRJURINLUOTO
                break
            else:
                print("Cinderella has nothing to give.")

        elif choice == "keep pumpkin":
            print("Cinderella holds onto the pumpkin.")
            print("Her stomach growls loudly.")
            print("The bear looks at her... then slowly shakes its head.")
            print("It does not move.")
            print("She cannot cross the bridge like this.")

        else:
            print("Invalid choice.")