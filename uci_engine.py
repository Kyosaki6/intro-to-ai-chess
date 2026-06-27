#!/usr/bin/env python3
import sys
import chess
import search


ENGINE_NAME = "ChessAI-Minimax"
ENGINE_AUTHOR = "IntroAI"
DEFAULT_DEPTH = 3
MAX_MOVES_ESTIMATE = 40


def main():
    board = chess.Board()
    depth = DEFAULT_DEPTH

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue

        if line == "uci":
            print(f"id name {ENGINE_NAME}")
            print(f"id author {ENGINE_AUTHOR}")
            print("option name Depth type spin default 3 min 1 max 10")
            print("uciok", flush=True)

        elif line == "isready":
            print("readyok", flush=True)

        elif line == "ucinewgame":
            board = chess.Board()

        elif line == "quit":
            break

        elif line.startswith("position"):
            parts = line.split()
            if len(parts) < 2:
                continue

            if parts[1] == "startpos":
                board = chess.Board()
                idx = 2
            elif parts[1] == "fen":
                fen = " ".join(parts[2:8])
                board = chess.Board(fen)
                idx = 8
            else:
                continue

            if idx < len(parts) and parts[idx] == "moves":
                for move_str in parts[idx + 1:]:
                    move = chess.Move.from_uci(move_str)
                    if move in board.legal_moves:
                        board.push(move)

        elif line.startswith("go"):
            args = line.split()
            go_depth = depth
            time_limit = None

            if "depth" in args:
                go_depth = int(args[args.index("depth") + 1])
            elif "movetime" in args:
                ms = int(args[args.index("movetime") + 1])
                time_limit = ms / 1000.0
            elif "wtime" in args or "btime" in args:
                time_limit = _calculate_time_limit(args)

            print(f"info string Searching depth={go_depth}{' time=' + str(time_limit) + 's' if time_limit else ''}...",
                  flush=True)
            move = search.get_best_move(board, depth=go_depth, time_limit=time_limit)
            print(f"info string Nodes searched: {search.NODES_SEARCHED}", flush=True)
            if move:
                print(f"bestmove {move.uci()}", flush=True)
            else:
                print("bestmove 0000", flush=True)

        elif line.startswith("setoption"):
            parts = line.split()
            if "Depth" in parts:
                idx = parts.index("Depth") + 2
                if idx < len(parts):
                    try:
                        depth = int(parts[idx])
                    except ValueError:
                        pass


def _calculate_time_limit(args: list) -> float:
    time_map = {}
    for key in ("wtime", "btime", "inc", "movetime"):
        if key in args:
            time_map[key] = int(args[args.index(key) + 1])

    if "movetime" in time_map:
        return time_map["movetime"] / 1000.0

    remaining = min(
        time_map.get("wtime", 999999),
        time_map.get("btime", 999999),
    )
    increment = time_map.get("inc", 0)
    budget = remaining / MAX_MOVES_ESTIMATE + increment
    return budget / 1000.0


if __name__ == "__main__":
    main()
