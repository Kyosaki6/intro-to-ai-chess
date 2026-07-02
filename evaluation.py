"""
evaluation.py - Hàm đánh giá bàn cờ cho Engine cờ vua
Tác giả: Person 2
"""

import chess

# ---------- GIÁ TRỊ QUÂN CƠ ----------
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# ---------- BẢN ĐỒ VỊ TRÍ (PST) ----------
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

PST = {
    chess.PAWN: PAWN_PST,
    chess.KNIGHT: KNIGHT_PST,
    chess.BISHOP: BISHOP_PST,
    chess.ROOK: ROOK_PST,
    chess.QUEEN: QUEEN_PST,
}

# ---------- HÀM PHỤ TRỢ ----------
def game_phase(board: chess.Board) -> float:
    total_pieces = 0
    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        total_pieces += len(board.pieces(piece_type, chess.WHITE)) + len(board.pieces(piece_type, chess.BLACK))
    phase = (total_pieces - 10) / 22
    return max(0.0, min(1.0, phase))

def get_pst(piece_type: int, square: int, color: bool, phase: float) -> int:
    if piece_type == chess.KING:
        idx = square if color == chess.WHITE else square ^ 56
        mid = KING_PST_MIDGAME[idx]
        end = KING_PST_ENDGAME[idx]
        return int(mid * phase + end * (1 - phase))
    else:
        table = PST[piece_type]
        idx = square if color == chess.WHITE else square ^ 56
        return table[idx]

# ---------- HÀM ĐÁNH GIÁ CHÍNH ----------
def evaluate_board(board: chess.Board) -> float:
    # Các trường hợp kết thúc
    if board.is_checkmate():
        return -float('inf') if board.turn == chess.WHITE else float('inf')
    if board.is_stalemate() or board.is_insufficient_material():
        return 0.0

    phase = game_phase(board)
    score = 0.0

    # Duyệt quân cờ
    for square, piece in board.piece_map().items():
        material = PIECE_VALUES[piece.piece_type]
        position = get_pst(piece.piece_type, square, piece.color, phase)
        if piece.color == chess.WHITE:
            score += material + position
        else:
            score -= material + position

    # Bishop pair
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += 40
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= 40

    # Rook on open file
    for sq in board.pieces(chess.ROOK, chess.WHITE):
        file = chess.square_file(sq)
        has_pawn = any(
            board.piece_at(s) and board.piece_at(s).piece_type == chess.PAWN
            for s in chess.SquareSet(chess.BB_FILES[file])
        )
        if not has_pawn:
            score += 20

    for sq in board.pieces(chess.ROOK, chess.BLACK):
        file = chess.square_file(sq)
        has_pawn = any(
            board.piece_at(s) and board.piece_at(s).piece_type == chess.PAWN
            for s in chess.SquareSet(chess.BB_FILES[file])
        )
        if not has_pawn:
            score -= 20

    # Mobility
    white_mobility = 0
    black_mobility = 0
    for move in board.legal_moves:
        if board.color_at(move.from_square) == chess.WHITE:
            white_mobility += 1
        else:
            black_mobility += 1
    score += (white_mobility - black_mobility) * 5

    # LUÔN TRẢ VỀ GIÁ TRỊ (float)
    return float(score)