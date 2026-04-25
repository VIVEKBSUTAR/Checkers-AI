import pygame
import sys
from menu import run_menu
from game_human_vs_ai import run_human_vs_ai
from game_ai_vs_ai import run_ai_vs_ai


def main():
    pygame.init()
    while True:
        mode, depth = run_menu()
        if mode == 'human_vs_ai':
            run_human_vs_ai(depth)
        elif mode == 'ai_vs_ai':
            run_ai_vs_ai(depth)


if __name__ == "__main__":
    main()
