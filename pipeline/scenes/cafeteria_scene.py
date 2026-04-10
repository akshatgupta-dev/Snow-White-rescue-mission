from pipeline.game_foundation import (
    SCENE_BEAR_BRIDGE,
    ITEM_PUMPKIN,
    ITEM_CARRIAGE,
    STATE_HAS_CARRIAGE,
    add_item,
    has_item,
    transform_item,
)


def play_cafeteria_scene(state):
    print("\n--- SAMK Cafeteria ---")
    print("Cinderella steps into the cafeteria.")
    print("It is late at night, and the whole place is strangely quiet.")
    print("The lights buzz softly overhead.")
    print("In the middle of an empty table sits a beautiful pumpkin.")

    while True:
        print("\nChoices: look around, inspect pumpkin, take pumpkin, leave")
        choice = input("> ").strip().lower()

        if choice == "look around":
            print("The cafeteria is dark and silent.")
            print("There is no food, no staff, and no students anywhere.")
            print("Only the pumpkin seems to be waiting for Cinderella.")

        elif choice == "inspect pumpkin":
            print("The pumpkin looks unusually perfect.")
            print("Its orange skin shines under the cafeteria lights.")
            print("Cinderella feels a little suspicious...")
            print("...but also very hungry.")

        elif choice == "take pumpkin":
            if not has_item(state, ITEM_PUMPKIN) and not has_item(state, ITEM_CARRIAGE):
                add_item(state, ITEM_PUMPKIN)
                print("Cinderella picks up the pumpkin carefully.")
                print("She is just about to take a bite...")

                print("\nThe clock strikes 10:00 PM.")
                print("A strange magic fills the cafeteria.")
                print("The pumpkin glows, shakes, and suddenly transforms!")

                if transform_item(state, ITEM_PUMPKIN, ITEM_CARRIAGE, STATE_HAS_CARRIAGE):
                    print("The pumpkin becomes a magical carriage.")
                    print('Cinderella stares at it for a moment.')
                    print('"…ok. Magic."')
                    print("Without waiting for an explanation, she climbs in.")
                    state.current_scene = SCENE_BEAR_BRIDGE
                    break
            else:
                print("Cinderella already dealt with the pumpkin.")

        elif choice == "leave":
            print("Cinderella looks at the pumpkin again.")
            print("No. That has to be important.")
            print("She decides not to leave yet.")

        else:
            print("Invalid choice.")