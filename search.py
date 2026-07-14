import chess
from evaluation import evaluate_board
from opening_book import get_opening_move

NODES_SEARCHED = 0


def get_best_move(board: chess.Board, depth: int = 3, use_opening_book: bool = True) -> chess.Move | None:
    global NODES_SEARCHED

    if use_opening_book and not board.is_game_over():
        book_move = get_opening_move(board)
        if book_move is not None:
            return book_move

    NODES_SEARCHED = 0

    is_maximizing = board.turn == chess.WHITE
    best_move = None

    if is_maximizing:
        best_score = -float("inf")
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, False)
            board.pop()
            if score > best_score:
                best_score = score
                best_move = move
    else:
        best_score = float("inf")
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, True)
            board.pop()
            if score < best_score:
                best_score = score
                best_move = move

    return best_move


def minimax(board: chess.Board, depth: int, is_maximizing: bool) -> float:
    global NODES_SEARCHED
    NODES_SEARCHED += 1

    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if is_maximizing:
        max_score = -float("inf")
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, False)
            board.pop()
            if score > max_score:
                max_score = score
        return max_score
    else:
        min_score = float("inf")
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, True)
            board.pop()
            if score < min_score:
                min_score = score
        return min_score
