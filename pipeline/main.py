from src.game_foundation import create_new_game


def main():
    print("Game starting...")
    state = create_new_game()
    print(state)


if __name__ == "__main__":
    main()