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
# Định dáng bảng trực quan: Rank 8 ở trên cùng (index 0), Rank 1 ở dưới cùng (index 56)
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

# ĐÃ SỬA: Bảng khai cuộc/trung cuộc chuẩn giúp Vua ẩn nấp ở góc nhập thành
KING_PST_MIDGAME = [
    -30,-40,-40,-50,-50,-40,-40,-30, # Rank 8
    -30,-40,-40,-50,-50,-40,-40,-30, # Rank 7
    -30,-40,-40,-50,-50,-40,-40,-30, # Rank 6
    -30,-40,-40,-50,-50,-40,-40,-30, # Rank 5
    -20,-30,-30,-40,-40,-30,-30,-20, # Rank 4
    -10,-20,-20,-20,-20,-20,-20,-10, # Rank 3
     20, 20,  0,  0,  0,  0, 20, 20, # Rank 2
     20, 30, 10,  0,  0, 10, 30, 20  # Rank 1 (Castling Zone)
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

# ---------- GAME PHASE ----------
def game_phase(board: chess.Board) -> float:
    phase = 0.0
    phase += len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK))
    phase += len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK))
    phase += (len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK))) * 2
    phase += (len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))) * 4
    max_phase = 24.0
    return max(0.0, min(1.0, phase / max_phase))

# ---------- PST LOOKUP ----------
def get_pst(piece_type: int, square: int, color: bool, phase: float) -> int:
    # ĐÃ SỬA: Đảo ngược lại phép XOR để khớp với cách lưu mảng từ Rank 8 -> Rank 1
    idx = square ^ 56 if color == chess.WHITE else square
    
    if piece_type == chess.KING:
        mid = KING_PST_MIDGAME[idx]
        end = KING_PST_ENDGAME[idx]
        return int(mid * phase + end * (1 - phase))
    else:
        return PST[piece_type][idx]

# ---------- MAIN EVALUATION ----------
def evaluate_board(board: chess.Board) -> float:
    if board.is_checkmate():
        return -99999.0 if board.turn == chess.WHITE else 99999.0
    if board.is_stalemate() or board.is_insufficient_material():
        return 0.0

    phase = game_phase(board)
    score = 0.0

    w_pawns_all = board.pieces(chess.PAWN, chess.WHITE)
    b_pawns_all = board.pieces(chess.PAWN, chess.BLACK)
    all_pawns = w_pawns_all | b_pawns_all

    # 1. Điểm lực lượng + Vị trí (Điểm tuyệt đối cho Minimax)
    for square, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type] + get_pst(piece.piece_type, square, piece.color, phase)
        score += val if piece.color == chess.WHITE else -val

    # 2. Cặp Tượng
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += 40
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= 40

    # 3. Xe chiếm cột mở
    for sq in board.pieces(chess.ROOK, chess.WHITE):
        if not (all_pawns & chess.BB_FILES[chess.square_file(sq)]):
            score += 20
    for sq in board.pieces(chess.ROOK, chess.BLACK):
        if not (all_pawns & chess.BB_FILES[chess.square_file(sq)]):
            score -= 20

    # 4. Cấu trúc Tốt
    for file_idx in range(8):
        file_mask = chess.BB_FILES[file_idx]
        w_pawns = w_pawns_all & file_mask
        b_pawns = b_pawns_all & file_mask

        w_cnt = len(w_pawns)
        b_cnt = len(b_pawns)
        
        # Phạt tốt chồng
        if w_cnt > 1:
            score -= 15 * (w_cnt - 1)
        if b_cnt > 1:
            score += 15 * (b_cnt - 1)

        # Phạt tốt cô lập
        adj_mask = 0
        if file_idx > 0:
            adj_mask |= chess.BB_FILES[file_idx - 1]
        if file_idx < 7:
            adj_mask |= chess.BB_FILES[file_idx + 1]

        if w_pawns and not (w_pawns_all & adj_mask):
            score -= 20 * w_cnt
        if b_pawns and not (b_pawns_all & adj_files_mask if 'adj_files_mask' in locals() else b_pawns_all & adj_mask):
            score += 20 * b_cnt

    return score