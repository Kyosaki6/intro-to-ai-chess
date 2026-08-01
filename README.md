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
- **Search:** Minimax with Alpha-Beta pruning, Iterative Deepening, Zobrist Transposition Table, Quiescence Search (TT, checks, delta pruning, max 4 ply)
- **Move ordering:** MVV-LVA (Most Valuable Victim - Least Valuable Attacker), TT best move promotion
- **Time management:** 95% hard deadline, 80% soft break for iterative deepening
- **Evaluation:** Material + Piece-Square Tables (PST), tapered game phase eval for King, Bishop pair (+40), Rook on open file (+20), Doubled pawn penalty (-15), Isolated pawn penalty (-20), Bishop blocking center pawn penalty (-20)
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

DC Engine depth=3 vs Stockfish UCI_Elo=1320 (100 games, tc=60+0.5):

| Result | Games |
|--------|-------|
| DC wins | 25 |
| Draws | 8 |
| Stockfish wins | 67 |

Win rate: **29%** — Elo difference **-155.5 +/- 72.8**, LOS 0.0%, DrawRatio 8.0%.

By color (DC Engine):
- As White: 15 wins / 5 draws / 30 losses (35%)
- As Black: 10 wins / 3 draws / 37 losses (23%)

DC Engine remains weaker than 1320 Elo; see [DC Engine v1.2 release](https://github.com/Kyosaki6/intro-to-ai-chess/releases) for feature notes.

## Info

- **Language:** Python 3
- **Dependencies:** python-chess, pyglet
- **Testing:** [Cute Chess](https://cutechess.com/) for automated match play and Elo measurement
- **License:** MIT
