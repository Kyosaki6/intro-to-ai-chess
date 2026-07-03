import chess

# ---------- MATERIAL VALUES ----------
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# ---------- PST TABLES ----------
PAWN_PST = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_PST = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

# King PST – Midgame (hide near corners)
KING_PST_MIDGAME = [
    -30,-20,-10,  0,  0,-10,-20,-30,
    -20,-10,  0, 10, 10,  0,-10,-20,
    -10,  0, 20, 30, 30, 20,  0,-10,
      0, 10, 30, 40, 40, 30, 10,  0,
      0, 10, 30, 40, 40, 30, 10,  0,
    -10,  0, 20, 30, 30, 20,  0,-10,
    -20,-10,  0, 10, 10,  0,-10,-20,
    -30,-20,-10,  0,  0,-10,-20,-30
]

# King PST – Endgame (active in center)
KING_PST_ENDGAME = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

PST = {
    chess.PAWN: PAWN_PST,
    chess.KNIGHT: KNIGHT_PST,
    chess.BISHOP: BISHOP_PST,
    chess.ROOK: ROOK_PST,
    chess.QUEEN: QUEEN_PST,
}

# ---------- GAME PHASE (FIXED: no pawns) ----------
def game_phase(board: chess.Board) -> float:
    """
    Calculate phase using only minor/major pieces.
    Max weight at start: 4 knights + 4 bishops + 4 rooks*2 + 2 queens*4 = 24
    """
    phase = 0.0
    phase += len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK))
    phase += len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK))
    phase += (len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK))) * 2
    phase += (len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))) * 4

    max_phase = 24.0
    return max(0.0, min(1.0, phase / max_phase))

# ---------- PST LOOKUP (with king tapering) ----------
def get_pst(piece_type: int, square: int, color: bool, phase: float) -> int:
    idx = square if color == chess.WHITE else square ^ 56
    if piece_type == chess.KING:
        mid = KING_PST_MIDGAME[idx]
        end = KING_PST_ENDGAME[idx]
        return int(mid * phase + end * (1 - phase))
    else:
        return PST[piece_type][idx]

# ---------- MAIN EVALUATION ----------
def evaluate_board(board: chess.Board) -> float:
    # Terminal states
    if board.is_checkmate():
        # Finite large constant – search will add/subtract depth to prefer shorter mates
        return -99999.0 if board.turn == chess.WHITE else 99999.0
    if board.is_stalemate() or board.is_insufficient_material():
        return 0.0

    phase = game_phase(board)
    score = 0.0

    # 1. Material + Positional (piece_map is fast)
    for square, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type] + get_pst(piece.piece_type, square, piece.color, phase)
        score += val if piece.color == chess.WHITE else -val

    # 2. Bishop pair
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += 40
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= 40

    # 3. Rook on open file – using bitboards (fast)
    all_pawns = board.pieces(chess.PAWN, chess.WHITE) | board.pieces(chess.PAWN, chess.BLACK)
    for sq in board.pieces(chess.ROOK, chess.WHITE):
        file_mask = chess.BB_FILES[chess.square_file(sq)]
        if not (all_pawns & file_mask):
            score += 20
    for sq in board.pieces(chess.ROOK, chess.BLACK):
        file_mask = chess.BB_FILES[chess.square_file(sq)]
        if not (all_pawns & file_mask):
            score -= 20

    # 4. Pawn structure – doubled pawns
    for file_idx in range(8):
        file_mask = chess.BB_FILES[file_idx]
        w_pawns = board.pieces(chess.PAWN, chess.WHITE) & file_mask
        b_pawns = board.pieces(chess.PAWN, chess.BLACK) & file_mask

        w_cnt = len(w_pawns)
        b_cnt = len(b_pawns)
        if w_cnt > 1:
            score -= 15 * (w_cnt - 1)
        if b_cnt > 1:
            score += 15 * (b_cnt - 1)

        # Isolated pawns
        adj_mask = 0
        if file_idx > 0:
            adj_mask |= chess.BB_FILES[file_idx - 1]
        if file_idx < 7:
            adj_mask |= chess.BB_FILES[file_idx + 1]

        if w_pawns and not (board.pieces(chess.PAWN, chess.WHITE) & adj_mask):
            score -= 20 * w_cnt
        if b_pawns and not (board.pieces(chess.PAWN, chess.BLACK) & adj_mask):
            score += 20 * b_cnt

    return score