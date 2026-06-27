#!/usr/bin/env python3
"""Test harness: play AI vs AI or AI vs random, print PGN + stats."""

import chess
import search
import sys
import time


def play_game(depth: int = 3, max_moves: int = 200) -> dict:
    board = chess.Board()
    moves = []

    for _ in range(max_moves):
        if board.is_game_over():
            break
        move = search.get_best_move(board, depth=depth)
        if move is None:
            break
        moves.append(move.uci())
        board.push(move)

    return {
        "moves": moves,
        "result": _result_str(board),
        "fen": board.fen(),
        "total_plies": len(moves),
        "nodes_searched": search.NODES_SEARCHED,
    }


def _result_str(board: chess.Board) -> str:
    if board.is_checkmate():
        return "0-1" if board.turn == chess.WHITE else "1-0"
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return "1/2-1/2"
    if board.is_game_over():
        return "*"
    return "*"


def test_position(fen: str, depth: int = 3, expected_move: str = None) -> None:
    board = chess.Board(fen)
    move = search.get_best_move(board, depth=depth)
    status = "OK" if expected_move is None or move.uci() == expected_move else "UNEXPECTED"
    print(f"  [{status:10}] FEN: {fen}")
    print(f"            Best move: {move}  (expected: {expected_move})  nodes={search.NODES_SEARCHED}")


def main():
    print("=" * 60)
    print("TEST 1: AI tự đấu (self-play, depth=3)")
    print("=" * 60)
    start = time.time()
    game = play_game(depth=3)
    elapsed = time.time() - start
    print(f"  Result: {game['result']}")
    print(f"  Plies:  {game['total_plies']}")
    print(f"  Nodes:  {game['nodes_searched']}")
    print(f"  Time:   {elapsed:.2f}s")
    print(f"  Moves:  {' '.join(game['moves'])}")
    print(f"  FEN:    {game['fen']}")
    print()

    print("=" * 60)
    print("TEST 2: AI depth=2 vs AI depth=3")
    print("=" * 60)
    board = chess.Board()
    for i in range(100):
        if board.is_game_over():
            break
        d = 2 if i % 2 == 0 else 3
        move = search.get_best_move(board, depth=d)
        if move is None:
            break
        board.push(move)
    print(f"  Result: {_result_str(board)}")
    print(f"  Plies:  {i + 1}")
    print(f"  FEN:    {board.fen()}")
    print()

    print("=" * 60)
    print("TEST 3: Kiểm tra nước đi trên các FEN cụ thể")
    print("=" * 60)
    test_position(
        "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2",
        depth=2,
        expected_move="e4d5",
    )
    test_position(
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
        depth=2,
        expected_move="e4e5",
    )
    test_position(
        "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        depth=2,
    )
    print()

    print("=" * 60)
    print("TEST 4: Tốc độ search (depth=3, 5 lần)")
    print("=" * 60)
    times = []
    nodes_list = []
    for i in range(5):
        board = chess.Board()
        start = time.time()
        move = search.get_best_move(board, depth=3)
        elapsed = time.time() - start
        times.append(elapsed)
        nodes_list.append(search.NODES_SEARCHED)
        print(f"  Run {i+1}: {move}  {elapsed:.3f}s  {search.NODES_SEARCHED} nodes")
    print(f"  Avg: {sum(times)/len(times):.3f}s  {sum(nodes_list)//len(nodes_list)} nodes")
    print()

    print("=" * 60)
    print("TEST 5: Phát hiện chiếu hết")
    print("=" * 60)
    test_position(
        "rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 1 3",
        depth=2,
    )
    test_position(
        "rnbqkbnr/ppppp2p/7R/4P1p1/2B1P3/8/PPPP2PP/RNBQK2N b KQkq - 0 5",
        depth=2,
    )
    print()

    print("Done.")


if __name__ == "__main__":
    main()
