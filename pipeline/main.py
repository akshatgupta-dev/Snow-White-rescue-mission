from src.game_foundation import create_new_game
from pipeline.agora_scene import AgoraHallScene
from pipeline.scene1 import play_kirjurinluoto_scene
from pipeline.cafeteria_v2 import play_cafeteria_scene
from pipeline.bear_bridge_v2 import play_bear_bridge_scene
from pipeline.akshat import library_scene


def main():
    print("Game starting...")
    state = create_new_game()
    print(state)


if __name__ == "__main__":
    main()