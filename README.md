# intro-to-ai-chess

Chess AI project — coursework for **Introduction to Artificial Intelligence** at Phenikaa University.

## Features

### GUI (pyglet)
- Textured board, drag-and-drop piece movement
- Last move & check highlighting
- Countdown clocks (1/3/5/10/30 min)
- Modes: 2-player, vs AI, Board Editor, Settings
- Background music, sound effects
- Undo/Redo (Z/X keys), ESC to quit

### AI Engine
- **Search:** Minimax with Alpha-Beta pruning, Iterative Deepening, Zobrist Transposition Table, Quiescence Search (max 4 ply, delta pruning)
- **Move ordering:** MVV-LVA (Most Valuable Victim - Least Valuable Attacker), TT best move promotion
- **Time management:** 95% hard deadline, 80% soft break for iterative deepening
- **Evaluation:** Material + Piece-Square Tables (PST), tapered game phase eval for King, Bishop pair (+40), Rook on open file (+20), Doubled pawn penalty (-15), Isolated pawn penalty (-20)
- **Opening book:** Built-in book (~25 positions) + Polyglot `.bin` support

### UCI Protocol
UCI-compatible for use with Cute Chess, Arena, etc.
- `uci` / `uciok`, `isready` / `readyok`, `ucinewgame`
- `position startpos` / `position fen ...` / `... moves ...`
- `go depth N` / `go movetime N` / `go wtime... btime...`
- `setoption name Depth value N`

## Installation

```bash
# Requires Python 3.10+
pip install -r requirements.txt
```

## Usage

### Run GUI
```bash
python main.py
```

## Project Structure

```
├── main.py              # GUI entry point
├── search.py            # Search algorithms (Minimax + Alpha-Beta + ID + TT + QSearch)
├── evaluation.py        # Board evaluation function
├── opening_book.py      # Opening book (built-in + Polyglot)
├── uci_engine.py        # UCI protocol handler
├── gui/
│   ├── chess_gui.py     # pyglet GUI (1307 lines)
│   ├── constants.py     # GUI constants
│   └── audio.py         # Procedural WAV sound generation
├── assets/              # Piece images, board texture
├── sounds/              # Sound files
└── requirements.txt     # python-chess, pyglet
```

## Elo Test Results

DC Engine depth=3 vs Stockfish UCI_Elo=1320 (20 games, tc=60+0.5):

| Result | Games |
|--------|-------|
| DC wins | 3 |
| Draws | 0 |
| Stockfish wins | 17 |

Win rate: **15%** — DC Engine may be weaker than 1320 Elo.

## Info

- **Language:** Python 3
- **Dependencies:** python-chess, pyglet
- **Testing:** [Cute Chess](https://cutechess.com/) for automated match play and Elo measurement
- **License:** MIT
