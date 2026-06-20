import chess
from evaluation import evaluate_board

NODES_SEARCHED = 0


def get_best_move(board: chess.Board, depth: int = 3) -> chess.Move | None:
    global NODES_SEARCHED
    NODES_SEARCHED = 0

    best_move = None
    if board.turn == chess.WHITE:
        best_score = float("-inf")
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, float("-inf"), float("inf"), False)
            board.pop()
            if score > best_score:
                best_score = score
                best_move = move
    else:
        best_score = float("inf")
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, float("-inf"), float("inf"), True)
            board.pop()
            if score < best_score:
                best_score = score
                best_move = move

    return best_move


def minimax(board: chess.Board, depth: int, alpha: float, beta: float,
            is_maximizing: bool) -> float:
    global NODES_SEARCHED
    NODES_SEARCHED += 1

    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if is_maximizing:
        max_score = float("-inf")
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_score = max(max_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_score
    else:
        min_score = float("inf")
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_score = min(min_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_score
