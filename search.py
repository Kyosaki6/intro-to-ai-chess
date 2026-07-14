import chess
from evaluation import evaluate_board
from opening_book import get_opening_move


class TimeoutException(Exception):
    pass


TT: dict = {}
NODES_SEARCHED = 0


def get_best_move(board: chess.Board, depth: int = 3, use_opening_book: bool = True) -> chess.Move | None:
    global NODES_SEARCHED

    if use_opening_book and not board.is_game_over():
        book_move = get_opening_move(board)
        if book_move is not None:
            return book_move

    NODES_SEARCHED = 0
    if len(TT) > 1000000:
        TT.clear()

    legal_moves_list = list(board.legal_moves)
    if not legal_moves_list:
        return None

    is_maximizing = board.turn == chess.WHITE
    best_move = legal_moves_list[0]
    start_time = time.time()
    deadline = start_time + time_limit * 0.95 if time_limit else float("inf")

    for d in range(1, depth + 1):
        if time_limit is not None and time.time() - start_time > time_limit * 0.8 and d > 1:
            break

        alpha = -float("inf")
        beta = float("inf")
        current_best = None

        ordered_moves = _order_moves(board, legal_moves_list)
        if best_move is not None and ordered_moves and ordered_moves[0] != best_move:
            try:
                idx = ordered_moves.index(best_move)
                ordered_moves[0], ordered_moves[idx] = ordered_moves[idx], ordered_moves[0]
            except ValueError:
                pass

        try:
            if is_maximizing:
                best_score = -float("inf")
                for move in ordered_moves:
                    board.push(move)
                    score = minimax(board, d - 1, alpha, beta, False, deadline)
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
                    score = minimax(board, d - 1, alpha, beta, True, deadline)
                    board.pop()
                    if score < best_score:
                        best_score = score
                        current_best = move
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
            best_move = current_best
        except TimeoutException:
            break

    return best_move


MAX_Q_PLY = 4
DELTA_MARGIN = PIECE_VALUES[chess.PAWN] + 50


def minimax(board: chess.Board, depth: int, alpha: float, beta: float,
            is_maximizing: bool, deadline: float = float("inf")) -> float:
    global NODES_SEARCHED
    NODES_SEARCHED += 1

    if NODES_SEARCHED & 0x3FF == 0 and time.time() > deadline:
        raise TimeoutException

    if board.is_repetition(2) or board.can_claim_draw():
        return 0.0

    key = zobrist_hash(board)
    tt_entry = TT.get(key)
    if tt_entry and tt_entry.depth >= depth:
        if tt_entry.flag == "exact":
            return tt_entry.score
        elif tt_entry.flag == "lower":
            alpha = max(alpha, tt_entry.score)
        elif tt_entry.flag == "upper":
            beta = min(beta, tt_entry.score)
        if alpha >= beta:
            return tt_entry.score

    if depth == 0 or board.is_game_over():
        if board.is_game_over():
            if board.is_checkmate():
                return -99999 - depth if board.turn == chess.WHITE else 99999 + depth
            return 0
        return quiescence_search(board, alpha, beta, is_maximizing, 0, deadline)

    ordered_moves = _order_moves(board, board.legal_moves)
    if tt_entry and tt_entry.best_move and tt_entry.best_move in board.legal_moves:
        ordered_moves = [tt_entry.best_move] + [m for m in ordered_moves if m != tt_entry.best_move]

    if is_maximizing:
        alpha_orig = alpha
        max_score = -float("inf")
        best_move_in_node = None
        for move in ordered_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False, deadline)
            board.pop()
            if score > max_score:
                max_score = score
                best_move_in_node = move
            alpha = max(alpha, score)
            if beta <= alpha:
                TT[key] = TTEntry(depth, max_score, "lower", best_move_in_node)
                return max_score
        flag = "exact" if max_score > alpha_orig else "upper"
        TT[key] = TTEntry(depth, max_score, flag, best_move_in_node)
        return max_score
    else:
        beta_orig = beta
        min_score = float("inf")
        best_move_in_node = None
        for move in ordered_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, True, deadline)
            board.pop()
            if score < min_score:
                min_score = score
                best_move_in_node = move
            beta = min(beta, score)
            if beta <= alpha:
                TT[key] = TTEntry(depth, min_score, "upper", best_move_in_node)
                return min_score
        flag = "exact" if min_score < beta_orig else "lower"
        TT[key] = TTEntry(depth, min_score, flag, best_move_in_node)
        return min_score


def quiescence_search(board: chess.Board, alpha: float, beta: float,
                      is_maximizing: bool, ply: int = 0,
                      deadline: float = float("inf")) -> float:
    global NODES_SEARCHED
    NODES_SEARCHED += 1

    if NODES_SEARCHED & 0x3FF == 0 and time.time() > deadline:
        raise TimeoutException

    if board.is_game_over():
        if board.is_checkmate():
            return -99999 + ply if board.turn == chess.WHITE else 99999 - ply
        return 0

    if ply > MAX_Q_PLY:
        return evaluate_board(board)

    stand_pat = evaluate_board(board)

    if is_maximizing:
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        captures = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
        captures = _order_moves(board, captures)
        for move in captures:
            attacker = board.piece_at(move.from_square)
            if board.is_en_passant(move):
                victim_val = PIECE_VALUES[chess.PAWN]
            else:
                victim = board.piece_at(move.to_square)
                victim_val = PIECE_VALUES[victim.piece_type] if victim else 0
            gain = PIECE_VALUES[move.promotion] if move.promotion else 0
            if stand_pat + victim_val + gain + DELTA_MARGIN < alpha:
                continue
            if victim_val > 0 and attacker and victim_val < PIECE_VALUES[attacker.piece_type]:
                if stand_pat + PIECE_VALUES[chess.PAWN] < alpha:
                    continue
            board.push(move)
            score = quiescence_search(board, alpha, beta, False, ply + 1, deadline)
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

        captures = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
        captures = _order_moves(board, captures)
        for move in captures:
            attacker = board.piece_at(move.from_square)
            if board.is_en_passant(move):
                victim_val = PIECE_VALUES[chess.PAWN]
            else:
                victim = board.piece_at(move.to_square)
                victim_val = PIECE_VALUES[victim.piece_type] if victim else 0
            gain = PIECE_VALUES[move.promotion] if move.promotion else 0
            if stand_pat - victim_val - gain - DELTA_MARGIN > beta:
                continue
            if victim_val > 0 and attacker and victim_val < PIECE_VALUES[attacker.piece_type]:
                if stand_pat - PIECE_VALUES[chess.PAWN] > beta:
                    continue
            board.push(move)
            score = quiescence_search(board, alpha, beta, True, ply + 1, deadline)
            board.pop()
            if score <= alpha:
                return alpha
            if score < beta:
                beta = score
        return beta
