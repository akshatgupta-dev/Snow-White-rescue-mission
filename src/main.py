import sys
from game_foundation import *
from scene1 import library_scene

def main():
    # Initialize a new game state
    state = create_new_game()
    
    print("Welcome to the Snow White Rescue Mission!")
    print(f"Character: {CHAR_CINDERELLA}")
    
    # Simple Game Loop
    while state.health > 0:
        if state.current_scene == SCENE_START:
            # Move to the first actual room
            state.current_scene = SCENE_LIBRARY
            
        elif state.current_scene == SCENE_LIBRARY:
            library_scene(state)
            
        elif state.current_scene == SCENE_AGORA:
            print("\nCongratulations! You made it to the Agora Hall.")
            print("To be continued in the next module...")
            break
            
        # Check for Lose Condition
        if state.health <= 0:
            print("\n" + "!"*30)
            print("GAME OVER: Cinderella has fallen.")
            print("!"*30)
            sys.exit()

if __name__ == "__main__":
    main()
