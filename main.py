import checkers
import gamebot
from time import sleep

## COLORS ##
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
HIGH = (160, 190, 255)

## DIRECTIONS ##
NORTHWEST = "northwest"
NORTHEAST = "northeast"
SOUTHWEST = "southwest"
SOUTHEAST = "southeast"


def main():
    while True:
        game = checkers.Game(loop_mode=True)
        game.setup()

        # AI plays RED
        bot = gamebot.Bot(
            game,
            RED,
            mid_eval='piece_and_board',
            end_eval='sum_of_dist',
            method='alpha_beta',
            depth=3
        )

        while True:
            # Main game loop

            if game.turn == BLUE:
                # Human turn
                game.player_turn()
                game.update()

            else:
                # AI turn
                print("AI thinking...")
                count_nodes = bot.step(game.board, True)
                print('Total nodes explored in this step are', count_nodes)
                game.update()

            if game.endit:
                break


if __name__ == "__main__":
    main()