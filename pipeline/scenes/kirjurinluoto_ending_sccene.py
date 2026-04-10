from pipeline.game_foundation import *

def play_kirjurinluoto_scene(state):
    if not get_flag(state, STATE_BEAR_ALLOWED_PASSAGE):
        print("The Guardian of Pori restricts your passage into Kirjurinjuoto! FOR NOW...")
        return
    
    print("/n            KIRJURINLUOTO             /n")
    print("Fog covers the park. Strange magic creates false paths.")
    print("Cinderella must choose the correct way forward.")
    
    while True:
        choice = input("Choose a path (left / center / right): ").strip().lower()

        if choice == "center":
            print("\nCinderella stays calm and follows the correct path through the fog.")
            print("At the center of Kirjurinluoto, the Evil Queen is waiting on a stage.")
            break

        elif choice in ["left", "right"]:
            state.health -= 10
            print("\nThat was a false path. The fog confuses Cinderella.")
            print(f"Health: {state.health}")

            if state.health <= 0:
                print("\nCinderella is lost in the fog. Game over.")
                return

        else:
            print("\nInvalid choice. Try again.")

    evil_queen_battle(state)
    
def evil_queen_battle(state):
    print("\n=== Evil Queen Battle ===")
    print("The Evil Queen laughs dramatically from the stage.")

    if not has_item(state, ITEM_LIGHTSABER):
        print("Cinderella has no lightsaber.")
        print("Without the weapon from Agora Hall, she cannot defeat the Evil Queen.")
        print("Game over.")
        state.health = 0
        return

    while True:
        choice = input("What do you do? (attack / defend / talk): ").strip().lower()

        if choice == "attack":
            print("\nCinderella uses the lightsaber.")
            print("The Evil Queen is defeated, and her magic disappears.")
            set_flag(state, STATE_QUEEN_DEFEATED, True)
            rescue_snow_white(state)
            return

        elif choice == "defend":
            state.health -= 5
            print("\nCinderella blocks a magical attack, but loses some health.")
            print(f"Health: {state.health}")

            if state.health <= 0:
                print("\nCinderella collapses before she can win. Game over.")
                return

        elif choice == "talk":
            state.health -= 10
            print("\nThe Evil Queen is not interested in talking.")
            print("She attacks while Cinderella hesitates.")
            print(f"Health: {state.health}")

            if state.health <= 0:
                print("\nCinderella is defeated. Game over.")
                return

        else:
            print("\nInvalid choice. Try again.")
            
def rescue_snow_white(state):
    print("\n=== Final Chamber ===")
    print("Snow White is trapped inside magic.")
    print("Cinderella breaks the spell and frees her.")

    set_flag(state, STATE_SNOW_WHITE_RESCUED, True)
    state.current_scene = SCENE_FINAL

    play_final_scene(state)
    
    
def play_final_scene(state):
    print("\n=== Ending Scene ===")
    print("Snow White is rescued.")
    print("But both Cinderella and Snow White are suddenly very hungry.")
    print("Nearby, they notice a shiny apple.")

    if not has_item(state, ITEM_APPLE):
        add_item(state, ITEM_APPLE)

    while True:
        choice = input("Do you eat the apple? (yes / no): ").strip().lower()

        if choice == "yes":
            remove_item(state, ITEM_APPLE)
            set_flag(state, STATE_ATE_APPLE, True)
            state.health = min(100, state.health + 20)

            print("\nThe apple restores Cinderella's health.")
            print(f"Health: {state.health}")
            print("\nSnow White is rescued, and both leave feeling stronger.")
            print("Moral: Be kind. Exercise. Go study. And eat healthy.")
            return

        elif choice == "no":
            print("\nCinderella decides not to eat the apple.")
            print("Snow White is still rescued, and they safely leave Kirjurinluoto together.")
            print("Moral: Be kind. Exercise. Go study. And eat healthy.")
            return

        else:
            print("\nInvalid choice. Try again.")