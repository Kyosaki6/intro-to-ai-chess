#!/usr/bin/env python3
import sys
import chess
import search


ENGINE_NAME = "ChessAI-Minimax"
ENGINE_AUTHOR = "IntroAI"
DEFAULT_DEPTH = 3


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

        elif line == "stop":
            print("bestmove 0000", flush=True)

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
            if "depth" in args:
                go_depth = int(args[args.index("depth") + 1])
            elif "movetime" in args:
                ms = int(args[args.index("movetime") + 1])
                go_depth = _time_to_depth(ms)
            elif "wtime" in args or "btime" in args:
                go_depth = _time_control_to_depth(args)

            print(f"info string Searching depth {go_depth}...", flush=True)
            move = search.get_best_move(board, depth=go_depth)
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
                        print(f"info string Depth set to {depth}", flush=True)
                    except ValueError:
                        pass


def _time_to_depth(ms: int) -> int:
    if ms >= 5000:
        return 4
    elif ms >= 2000:
        return 3
    elif ms >= 500:
        return 2
    return 1


def _time_control_to_depth(args: list) -> int:
    time_map = {}
    for key in ("wtime", "btime", "movetime"):
        if key in args:
            time_map[key] = int(args[args.index(key) + 1])
    remaining = time_map.get("movetime") or min(
        time_map.get("wtime", 999999), time_map.get("btime", 999999)
    )
    return _time_to_depth(remaining // 60 if remaining > 60000 else remaining)


if __name__ == "__main__":
    main()
