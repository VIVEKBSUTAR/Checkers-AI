<div align="center">

# ♟ Checkers AI

**A fully-featured Checkers engine with an intelligent AI opponent, built in Python with Pygame.**

Minimax · Alpha-Beta Pruning · Game Tree Visualization · 4 Difficulty Levels · Human vs AI · AI vs AI

---

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.0%2B-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Game Modes](#game-modes)
- [AI Architecture](#ai-architecture)
- [Evaluation Functions](#evaluation-functions)
- [Game Tree Visualization](#game-tree-visualization)
- [Controls](#controls)
- [Technical Design](#technical-design)
- [Screenshots](#screenshots)
- [Academic Context](#academic-context)
- [Requirements](#requirements)

---

## Overview

Checkers AI is a complete implementation of the classic board game Checkers (also known as Draughts), featuring an intelligent AI opponent powered by the **Minimax algorithm with Alpha-Beta Pruning**. The project was built as an academic exploration of game-playing AI, demonstrating how decision-tree search algorithms can be applied to produce strong, efficient gameplay.

The project ships with a modern, animated dark-themed UI built entirely in Pygame, supporting two distinct game modes, four difficulty levels, a live **game tree visualization** that shows the AI's decision process in real time, and a step-by-step mode for educational walkthroughs.

---

## Features

### Gameplay
- Full standard Checkers rule implementation — legal move validation, mandatory captures, multi-jump chains, piece promotion to King, and endgame detection
- **Human vs AI** — play as BLUE against the RED AI opponent
- **AI vs AI** — watch two independent AI bots compete against each other
- 60 FPS smooth rendering with animated piece highlights, legal move indicators, and selection glows

### AI
- **Minimax algorithm** with configurable search depth
- **Alpha-Beta Pruning** — exponentially reduces the number of nodes explored without affecting move quality
- **Four difficulty levels** mapped to increasing search depths (Easy → Expert)
- **Phase-aware evaluation** — mid-game and endgame heuristics switch automatically when fewer than 8 pieces remain
- **Mobility bonus** — rewards positions with more available moves
- **Center control bonus** — incentivises occupying the four central squares
- **Positional evaluation** — weights pieces differently based on board half, row advancement, and king status

### UI & Visualization
- Fullscreen dark-themed interface with animated background
- Smooth screen transitions — fade-in on entry, fade-out on exit
- **Live Game Tree Visualization** — after each AI move, displays the top 4 candidate boards side by side, with staggered fade-in animation, score labels, and pulsing highlight on the chosen move
- **Pruned move display** — moves eliminated by Alpha-Beta Pruning appear as red crossed-out boards labelled "PRUNED — α-β cut"
- **Step Mode** — pause AI vs AI and advance one move at a time with a button or keyboard shortcut
- **Speed slider** — control AI vs AI playback speed from 0.1 to 3.0 seconds per move
- 3D sphere-shaded pieces with gold star crown for Kings
- Piece count progress bars and live stats in the sidebar

---

## Project Structure

```
Checkers-AI/
│
├── main.py                 # Entry point — initialises Pygame and routes between modes
├── menu.py                 # Main menu UI — difficulty selector, mode selector, animations
├── checkers.py             # Core game engine — Board, Piece, Square, Game, Graphics classes
├── gamebot.py              # AI engine — Minimax, Alpha-Beta Pruning, evaluation functions
├── game_human_vs_ai.py     # Human vs AI game loop — board rendering, sidebar, player input
├── game_ai_vs_ai.py        # AI vs AI game loop — game tree visualization, step mode, slider
│
├── resources/
│   └── board.png           # Board background image (used by legacy Graphics class)
│
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── __init__.py
```

### Module Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Top-level loop — calls `run_menu()`, routes to the selected game mode |
| `menu.py` | Fullscreen animated menu, difficulty/mode selection, fade transitions |
| `checkers.py` | Board state, legal move generation, piece movement, kinging, endgame detection |
| `gamebot.py` | All AI logic — search algorithms, evaluation functions, candidate generation |
| `game_human_vs_ai.py` | Human vs AI rendering and input handling |
| `game_ai_vs_ai.py` | AI vs AI rendering, game tree visualization, step mode, speed control |

---

## Installation

**Prerequisites:** Python 3.9 or higher.

```bash
# 1. Clone the repository
git clone https://github.com/VIVEKBSUTAR/Checkers-AI.git
cd Checkers-AI

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

`requirements.txt` contains:
```
pygame>=2.0.0
```

---

## How to Run

```bash
python main.py
```

The game opens in fullscreen. Use **ESC** at any time to return to the main menu.

---

## Game Modes

### Player vs AI

You play as **BLUE** (bottom of the board). The AI plays as **RED** (top of the board).

- Click a piece to select it — valid moves are shown as blue dots
- Click a destination square to move
- Multi-jump captures are chained automatically when available
- The sidebar displays: current turn, move count, nodes explored, AI search depth, piece count bars, and winner announcement

### AI vs AI

Two independent AI bots (both using Alpha-Beta Pruning) play against each other.

- The **main board** on the left shows the live game
- The **game tree panel** on the right shows the AI's decision process after each move
- Use the **speed slider** to control the delay between moves (0.1s to 3.0s)
- Switch to **Step Mode** to advance one move at a time

---

## AI Architecture

### Minimax Algorithm

Minimax is a recursive decision-tree search algorithm used in two-player zero-sum games. At each node the algorithm alternates between:

- **MAX nodes** — the AI tries to maximise its evaluation score (its own best move)
- **MIN nodes** — the AI assumes the opponent plays optimally to minimise the score

The tree is explored to a fixed depth (the difficulty level), and the leaf nodes are scored by the evaluation function. The best move is selected by propagating scores back up the tree.

```
          MAX (AI)
         /    \    \
       MIN    MIN   MIN    ← opponent's responses
      / \    / \   / \
    MAX MAX ...             ← AI's replies
```

### Alpha-Beta Pruning

Alpha-Beta Pruning is an optimisation of Minimax that eliminates branches which cannot possibly affect the final decision:

- **α (alpha)** — the best score the MAX player has found so far
- **β (beta)** — the best score the MIN player has found so far
- A branch is **pruned** (skipped) when `β ≤ α` — the opponent will never allow this line

In practice, Alpha-Beta Pruning reduces the effective branching factor from `b` to approximately `√b`, allowing the AI to search roughly **twice as deep** in the same time compared to plain Minimax.

| Depth | Minimax nodes | Alpha-Beta nodes (approx.) | Speedup |
|---|---|---|---|
| 1 | ~7 | ~7 | 1× |
| 2 | ~49 | ~14 | 3.5× |
| 3 | ~343 | ~58 | 5.9× |
| 4 | ~2,401 | ~245 | 9.8× |
| 5 | ~16,807 | ~1,024 | 16.4× |

### Difficulty Levels

| Level | Search Depth | Character |
|---|---|---|
| Easy | 1 | Looks only one move ahead — near-random play |
| Medium | 2 | Considers immediate responses — basic strategy |
| Hard | 3 | Plans two moves ahead — solid, challenging opponent |
| Expert | 5 | Deep search with full heuristics — very hard to beat |

---

## Evaluation Functions

The AI uses heuristic evaluation functions to score board positions at leaf nodes. All functions score relative to the AI's colour (positive = AI advantage, negative = opponent advantage).

### Mid-Game: `piece_and_board` *(default)*

Scores each piece based on:

| Condition | Score |
|---|---|
| Friendly King | +10 |
| Enemy King | −10 |
| Friendly piece in own half | +5 |
| Friendly piece in enemy half | +7 |
| Enemy piece in own half | −7 |
| Enemy piece in enemy half | −5 |

**Additional bonuses applied on top:**

- **Mobility bonus** — `+0.5 × (own legal moves − opponent legal moves)`. Rewards positions with more available moves, penalises being cramped.
- **Center control bonus** — `+2` per friendly piece on the 4 central squares `(3,3)(4,3)(3,4)(4,4)`, `+1` for adjacent near-center squares. Mirror negative for enemy pieces. Central control is a known positional strength in Checkers.

### Other Available Functions

| Function | Description |
|---|---|
| `piece2val` | Simple piece count — pawn=1, king=2 |
| `piece_and_row` | Weights advancement toward promotion row |
| `piece_and_board_pov` | Normalised positional score divided by total piece count |

### Endgame: `sum_of_dist`

Activated automatically when fewer than 8 pieces remain on the board. Computes the sum of Euclidean distances between all pairs of friendly and enemy pieces. The AI minimises this distance when it has more pieces (chases the opponent) and maximises it when it has fewer (runs away).

```python
distance = √((x₁−x₂)² + (y₁−y₂)²)
```

---

## Game Tree Visualization

The AI vs AI mode includes a unique **real-time game tree visualizer** that makes the AI's decision process fully transparent.

### How it works

After each AI move, `get_top_candidates()` evaluates all legal moves and returns the top 4 by score, along with all pruned moves.

**Top row — 4 candidate boards:**
- Each mini board shows the resulting position if that move were played
- The **★ CHOSEN** board (highest score) is highlighted with a pulsing green border
- Each board displays its evaluation score (`score: +22`, `score: +20`, etc.)
- Boards animate in with a staggered fade-in + slide-up effect (80ms delay between each)

**Bottom row — pruned moves:**
- Moves eliminated by Alpha-Beta Pruning appear as red crossed-out boxes
- Labelled "PRUNED — α-β cut" to explain why they were discarded
- The count of eliminated moves is shown (e.g. "α-β PRUNED: 4 moves eliminated")

**Connector lines** from the root position dot to each candidate board show the tree structure visually.

### Step Mode

Switch to **Step Mode** using the toggle button (or press `→` to advance). The AI pauses after every move, allowing you to:
- Study the candidate boards at your own pace
- Understand which move was chosen and why
- Compare scores across the 4 options
- See exactly which moves were pruned

---

## Controls

### Menu
| Action | Control |
|---|---|
| Select difficulty | Click Easy / Medium / Hard / Expert |
| Start Player vs AI | Click PLAYER vs AI |
| Start AI vs AI | Click AI vs AI |
| Quit | Click QUIT or press ESC |

### Player vs AI
| Action | Control |
|---|---|
| Select piece | Left click on your piece |
| Move piece | Left click destination square |
| Return to menu | ESC or ← MAIN MENU button |
| Restart | ↺ RESTART button |

### AI vs AI
| Action | Control |
|---|---|
| Pause / Resume | SPACE or ⏸ PAUSE button |
| Toggle Step Mode | STEP MODE button |
| Advance one move (Step Mode) | → key or ▶ NEXT MOVE button |
| Adjust speed | Drag the Delay slider |
| Restart | ↺ RESTART button |
| Return to menu | ESC or ← MENU button |

---

## Technical Design

### Headless Game Mode

The `Game` class in `checkers.py` accepts a `skip_graphics=True` parameter. When set, `self.graphics = None` and all graphics method calls are guarded with `if self.graphics is not None`. This allows `game_ai_vs_ai.py` to run the game logic without creating a second Pygame window — the AI vs AI mode handles all rendering itself.

### Frame-Rate Independent Animation

All animations use `dt = clock.tick(60) / 1000.0` (delta time in seconds) so timings are consistent regardless of frame rate:

```python
# Example: ease-out cubic board slide
t    = min(1.0, phase_elapsed / 0.6)
ease = 1 - (1 - t) ** 3
cur_bx = int(START_BX + (BX - START_BX) * ease)
```

### Alpha Surface Rules

Per-pixel effects (piece glows, connector line fades) use `pygame.SRCALPHA` surfaces with alpha encoded in the colour tuple. Full-screen overlays (fade-in, fade-out, pause overlay) use plain `pygame.Surface` with `.set_alpha()` to avoid mixing the two modes on the same surface.

### Candidate Generation

`Bot.get_top_candidates(board, n=4)` runs a shallow Alpha-Beta search on each legal move, scores it, sorts descending, and returns the top `n` with their resulting board states. The best move is then applied to the real board via `_action()`. Rejected candidates (beyond top `n`) are returned separately for display in the pruned row.

---

## Screenshots

> *(Run the project to see the fullscreen animated UI in action.)*

| Screen | Description |
|---|---|
| Main Menu | Animated checkerboard background, difficulty selector with pulsing selected button, mode selector |
| Player vs AI | Game board with 3D pieces, sidebar with stats, piece bars, and live turn indicator |
| AI vs AI | Live board + 4 candidate mini boards + pruned row + speed slider + step mode |

---

## Academic Context

This project was developed as a **Semester 4 AI Course Project** exploring the following core concepts:

- **Game Theory** — zero-sum two-player games and the Minimax framework
- **Search Algorithms** — depth-limited tree search and the effect of depth on AI strength
- **Pruning** — Alpha-Beta Pruning as a provably correct optimisation of Minimax
- **Heuristic Evaluation** — designing evaluation functions for non-terminal game states
- **Positional Strategy** — mobility, center control, and endgame distance heuristics

### Key Observations

- Alpha-Beta Pruning reduces explored nodes by ~60–90% compared to plain Minimax at the same depth, with identical move quality
- At depth 3, the AI explores ~50–300 nodes per move depending on board complexity
- The `piece_and_board` evaluation with mobility and center bonuses outperforms simple piece-count evaluation in positional games
- Endgame switching (at <8 pieces) dramatically improves late-game play — the `sum_of_dist` heuristic correctly drives the AI to chase or evade

---

## Requirements

```
pygame >= 2.0.0
Python >= 3.9
```

Install with:

```bash
pip install -r requirements.txt
```

No other external libraries are required. All game logic, AI, rendering, and animation are implemented using only the Python standard library and Pygame.

---

<div align="center">

Built with Python & Pygame · Minimax + Alpha-Beta Pruning · Academic AI Project

</div>
