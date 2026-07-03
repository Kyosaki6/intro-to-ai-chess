import chess
import time
from evaluation import evaluate_board, PIECE_VALUES

NODES_SEARCHED = 0


def _order_moves(board, moves):
    def _score(move):
        if board.is_capture(move):
            attacker = board.piece_at(move.from_square)
            a_val = PIECE_VALUES[attacker.piece_type] if attacker else 0
            if board.is_en_passant(move):
                victim_val = PIECE_VALUES[chess.PAWN]
            else:
                victim = board.piece_at(move.to_square)
                victim_val = PIECE_VALUES[victim.piece_type] if victim else 0
            return 10000 + victim_val * 10 - a_val
        if move.promotion:
            return 5000 + PIECE_VALUES[move.promotion]
        return 0
    return sorted(moves, key=_score, reverse=True)


def get_best_move(board: chess.Board, depth: int = 3,
                  time_limit: float | None = None) -> chess.Move | None:
    global NODES_SEARCHED
    NODES_SEARCHED = 0

    legal_moves_list = list(board.legal_moves)
    if not legal_moves_list:
        return None

    is_maximizing = board.turn == chess.WHITE
    best_move = legal_moves_list[0]
    start_time = time.time()

    for d in range(1, depth + 1):
        if time_limit is not None and time.time() - start_time > time_limit * 0.8 and d > 1:
            break

        alpha = -float("inf")
        beta = float("inf")
        current_best = None

        ordered_moves = _order_moves(board, legal_moves_list)
        if best_move is not None and ordered_moves:
            ordered_moves = [best_move] + [m for m in ordered_moves if m != best_move]

        if is_maximizing:
            best_score = -float("inf")
            for move in ordered_moves:
                board.push(move)
                score = minimax(board, d - 1, alpha, beta, False)
                board.pop()
                if score > best_score:
                    best_score = score
                    current_best = move
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
        else:
            best_score = float("inf")
            for move in ordered_moves:
                board.push(move)
                score = minimax(board, d - 1, alpha, beta, True)
                board.pop()
                if score < best_score:
                    best_score = score
                    current_best = move
                beta = min(beta, score)
                if beta <= alpha:
                    break

        best_move = current_best

    return best_move


MAX_Q_PLY = 4
DELTA_MARGIN = PIECE_VALUES[chess.PAWN] + 50


def minimax(board: chess.Board, depth: int, alpha: float, beta: float,
            is_maximizing: bool) -> float:
    global NODES_SEARCHED
    NODES_SEARCHED += 1

    if depth == 0 or board.is_game_over():
        if board.is_game_over():
            if board.is_checkmate():
                return -99999 - depth if board.turn == chess.WHITE else 99999 + depth
            return 0
        if board.is_repetition(2) or board.can_claim_draw():
            return 0.0
        return quiescence_search(board, alpha, beta, is_maximizing, ply=0)

    ordered_moves = _order_moves(board, board.legal_moves)

    if is_maximizing:
        max_score = -float("inf")
        for move in ordered_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if score > max_score:
                max_score = score
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_score
    else:
        min_score = float("inf")
        for move in ordered_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if score < min_score:
                min_score = score
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_score


def quiescence_search(board: chess.Board, alpha: float, beta: float,
                      is_maximizing: bool, ply: int = 0) -> float:
    global NODES_SEARCHED
    NODES_SEARCHED += 1

    if board.is_game_over():
        if board.is_checkmate():
            return -99999 + ply if board.turn == chess.WHITE else 99999 - ply
        return 0
    if board.is_repetition(2) or board.can_claim_draw():
        return 0.0

    if ply > MAX_Q_PLY:
        return evaluate_board(board)

    stand_pat = evaluate_board(board)

    if is_maximizing:
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        captures = [m for m in board.legal_moves if board.is_capture(m)]
        captures = _order_moves(board, captures)
        for move in captures:
            attacker = board.piece_at(move.from_square)
            if board.is_en_passant(move):
                victim_val = PIECE_VALUES[chess.PAWN]
            else:
                victim = board.piece_at(move.to_square)
                victim_val = PIECE_VALUES[victim.piece_type] if victim else 0
            if stand_pat + victim_val + DELTA_MARGIN < alpha:
                continue
            if attacker and victim_val < PIECE_VALUES[attacker.piece_type]:
                if stand_pat + PIECE_VALUES[chess.PAWN] < alpha:
                    continue
            board.push(move)
            score = quiescence_search(board, alpha, beta, False, ply + 1)
            board.pop()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha
    else:
        if stand_pat <= alpha:
            return alpha
        if stand_pat < beta:
            beta = stand_pat

        captures = [m for m in board.legal_moves if board.is_capture(m)]
        captures = _order_moves(board, captures)
        for move in captures:
            attacker = board.piece_at(move.from_square)
            if board.is_en_passant(move):
                victim_val = PIECE_VALUES[chess.PAWN]
            else:
                victim = board.piece_at(move.to_square)
                victim_val = PIECE_VALUES[victim.piece_type] if victim else 0
            if stand_pat - victim_val - DELTA_MARGIN > beta:
                continue
            if attacker and victim_val < PIECE_VALUES[attacker.piece_type]:
                if stand_pat - PIECE_VALUES[chess.PAWN] > beta:
                    continue
            board.push(move)
            score = quiescence_search(board, alpha, beta, True, ply + 1)
            board.pop()
            if score <= alpha:
                return alpha
            if score < beta:
                beta = score
        return beta
