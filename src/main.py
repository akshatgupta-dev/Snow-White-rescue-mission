from agora_scene import AgoraHallScene
from pipeline.game_foundation import create_new_game


def run() -> None:
	state = create_new_game()
	scene = AgoraHallScene()
	print(scene.enter(state))


if __name__ == "__main__":
	run()
