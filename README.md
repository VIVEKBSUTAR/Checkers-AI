# Checkers AI

## Overview

This repository contains a checkers (draughts) game with an AI opponent built using the Minimax algorithm with alpha-beta pruning. The project includes:

1. A playable local checkers game using Pygame.
2. Board logic and legal move generation.
3. An AI player that evaluates positions and chooses moves.

## Features

1. Standard checkers movement, captures, multi-jumps, and king promotion.
2. Human vs AI gameplay.
3. Position evaluation based on piece count and king advantage.
4. Configurable AI search depth in code.

## Run Locally

Install dependencies and start the game:

```bash
pip install -r requirements.txt
python main.py
```

## Project Files

1. `main.py` - game entry point and loop.
2. `checkers.py` - board model, rules, and move generation.
3. `gamebot.py` - Minimax and alpha-beta pruning logic.
4. `resources/` - game board and assets.
5. `imgs/` - gameplay GIFs.

## Notes

This is a personal repository version prepared for independent use and updates.

## Repository

GitHub: https://github.com/VIVEKBSUTAR/Checkers-AI

## Issues

Report bugs or request features here:
https://github.com/VIVEKBSUTAR/Checkers-AI/issues
