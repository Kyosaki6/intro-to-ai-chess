import chess
import chess.polyglot
import random
from pathlib import Path


def _board_key(board):
    return board.fen().rsplit(" ", 2)[0]


def _build_builtin_book():
    book = {}
    board = chess.Board()

    def save(moves, entries):
        board.reset()
        for uci in moves:
            board.push_uci(uci)
        key = _board_key(board)
        book[key] = [(chess.Move.from_uci(uci), weight) for uci, weight in entries]

    save([], [("e2e4", 100), ("d2d4", 80), ("g1f3", 50), ("c2c4", 40)])

    save(["e2e4"], [("e7e5", 100), ("c7c5", 80), ("e7e6", 60), ("d7d6", 40), ("g8f6", 50), ("d7d5", 30)])

    save(["e2e4", "e7e5"], [("g1f3", 100), ("f1c4", 60), ("d2d4", 50), ("b1c3", 40)])

    save(["e2e4", "e7e5", "g1f3"], [("b8c6", 100), ("d7d6", 50), ("g8f6", 60)])

    save(["e2e4", "e7e5", "g1f3", "b8c6"], [("f1b5", 100), ("f1c4", 60), ("d2d4", 50), ("b1c3", 40)])

    save(["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
         [("a7a6", 100), ("d7d6", 50), ("g8f6", 60), ("f8c5", 40)])

    save(["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
         [("g8f6", 50), ("f8c5", 100), ("f8e7", 20)])

    save(["e2e4", "c7c5"], [("g1f3", 100), ("d2d4", 60), ("b1c3", 50), ("c2c3", 30)])

    save(["e2e4", "c7c5", "g1f3"], [("d7d6", 100), ("b8c6", 80), ("e7e6", 60), ("g8f6", 40)])

    save(["e2e4", "e7e6"], [("d2d4", 100), ("g1f3", 40), ("d2d3", 30)])

    save(["e2e4", "e7e6", "d2d4", "d7d5"],
         [("b1d2", 60), ("b1c3", 100), ("e4e5", 50)])

    save(["e2e4", "c7c6"], [("d2d4", 100), ("b1c3", 30), ("g1f3", 20)])

    save(["e2e4", "c7c6", "d2d4", "d7d5"],
         [("b1d2", 60), ("b1c3", 100), ("e4e5", 40), ("e4d5", 30)])

    save(["e2e4", "d7d5"], [("e4d5", 100), ("e4e5", 50), ("b1c3", 20)])

    save(["d2d4"], [("d7d5", 100), ("g8f6", 70), ("f7f5", 30), ("e7e6", 20)])

    save(["d2d4", "d7d5"], [("c2c4", 100), ("g1f3", 60), ("b1c3", 40)])

    save(["d2d4", "d7d5", "c2c4"],
         [("e7e6", 100), ("c7c6", 60), ("d5c4", 50), ("g8f6", 40)])

    save(["d2d4", "d7d5", "c2c4", "e7e6"],
         [("b1c3", 100), ("g1f3", 60), ("c4d5", 30)])

    save(["d2d4", "d7d5", "c2c4", "c7c6"],
         [("g1f3", 80), ("b1c3", 100), ("e2e3", 30)])

    save(["d2d4", "g8f6"], [("c2c4", 100), ("g1f3", 60), ("b1c3", 40)])

    save(["d2d4", "g8f6", "c2c4"],
         [("g7g6", 100), ("e7e6", 80), ("d7d5", 40), ("b7b6", 30)])

    save(["d2d4", "g8f6", "c2c4", "g7g6"],
         [("b1c3", 100), ("g1f3", 60), ("e2e4", 40)])

    save(["d2d4", "g8f6", "c2c4", "e7e6"],
         [("b1c3", 100), ("g1f3", 60), ("g2g3", 40)])

    return book


BUILT_IN_BOOK = _build_builtin_book()

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        for f in sorted(Path.cwd().glob("*.bin")):
            try:
                _reader = chess.polyglot.open_reader(str(f))
                break
            except Exception:
                continue
    return _reader


def get_opening_move(board, max_depth=10):
    if board.fullmove_number > max_depth:
        return None

    reader = _get_reader()
    if reader is not None:
        try:
            entries = list(reader.find_all(board))
            if entries:
                total = sum(e.weight for e in entries)
                r = random.randint(1, total)
                for entry in entries:
                    r -= entry.weight
                    if r <= 0:
                        return entry.move
                return entries[-1].move
        except Exception:
            pass

    key = _board_key(board)
    entries = BUILT_IN_BOOK.get(key)
    if entries:
        total = sum(w for _, w in entries)
        r = random.randint(1, total)
        for move, weight in entries:
            r -= weight
            if r <= 0:
                if move in board.legal_moves:
                    return move

    return None
