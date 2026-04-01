from src.game_foundation import *

def library_scene(state):
   
    print("\n" + "="*30)
    print("LOCATION: THE LIBRARY")
    print("="*30)
    print("Cinderella enters the silent, dust-filled library.")
    print("A magical holographic guardian appears, blocking the exit.")
    print("'To receive the map and pass to the Agora Hall, you must prove your wisdom.'")
    
    # The Puzzle / Special Action
    print("\nGUARDIAN: 'What is the full form of SAMK?'")
    answer = input("Your answer: ").lower().strip()
    
    if "satakunta university of applied sciences" in answer:
        print("\n'Correct!' The guardian bows and vanishes, leaving a glowing map behind.")
        # Update state using foundation helpers
        add_item(state, ITEM_MAP)
        set_flag(state, STATE_HAS_MAP, True)
        
        # Transition to the next scene
        state.current_scene = SCENE_AGORA
        print(f"** You picked up the {ITEM_MAP}! **")
        print("The door to the Agora Hall is now unlocked.")
    else:
        print("\n'WRONG!' The guardian releases a burst of dark energy.")
        # Lose health as per design document
        state.health -= 10
        print("You have taken 10 damage!")