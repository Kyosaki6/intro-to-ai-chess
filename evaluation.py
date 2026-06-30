import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Piece-Square Tables from White's perspective
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10,-20,-20, 10, 10,  5,
    5, -5,-10,  0,  0,-10, -5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
    0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    5, 10, 10, 10, 10, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
    0,  0,  5,  5,  5,  5,  0, -5,
    -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_TABLE_MIDGAME = [
    20, 30, 10,  0,  0, 10, 30, 20,
    20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]

KING_TABLE_ENDGAME = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -20,-10,  0, 10, 10,  0,-10,-20,
    -10,  0, 10, 20, 20, 10,  0,-10,
    -10,  0, 10, 20, 20, 10,  0,-10,
    -20,-10,  0, 10, 10,  0,-10,-20,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -50,-40,-30,-20,-20,-30,-40,-50,
]

PST = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
}

def evaluate_board(board: chess.Board) -> float:
    score = 0
    
    # 1. Optimization: iterate only pieces
    white_bishops = 0
    black_bishops = 0
    
    # Calculate material for phase
    total_material = 0
    for piece in board.piece_map().values():
        if piece.piece_type != chess.PAWN and piece.piece_type != chess.KING:
            total_material += PIECE_VALUES[piece.piece_type]
            
    for square, piece in board.piece_map().items():
        # Material + PST
        material = PIECE_VALUES[piece.piece_type]
        sq_idx = square if piece.color == chess.WHITE else square ^ 56
        
        if piece.piece_type == chess.KING:
            # Tapered Evaluation for King
            # Use total material to determine phase
            # Max material for major/minor pieces is 4000.
            phase = max(0, min(1, (4000 - total_material) / 4000))
            mg = KING_TABLE_MIDGAME[sq_idx]
            eg = KING_TABLE_ENDGAME[sq_idx]
            position = int(mg * (1 - phase) + eg * phase)
        else:
            position = PST[piece.piece_type][sq_idx]
        
        if piece.color == chess.WHITE:
            score += (material + position)
            if piece.piece_type == chess.BISHOP: white_bishops += 1
        else:
            score -= (material + position)
            if piece.piece_type == chess.BISHOP: black_bishops += 1
            
        # Task 2: Rook on open file
        if piece.piece_type == chess.ROOK:
            file = chess.square_file(square)
            # Check if any pawns on this file
            all_pawns = board.pieces(chess.PAWN, chess.WHITE) | board.pieces(chess.PAWN, chess.BLACK)
            if not any(chess.square_file(p) == file for p in all_pawns):
                score += 20 if piece.color == chess.WHITE else -20
                
    # Bishop pair bonus
    if white_bishops >= 2: score += 50
    if black_bishops >= 2: score -= 50
    
    # Mobility bonus
    current_turn = board.turn
    
    board.turn = chess.WHITE
    white_mobility = board.legal_moves.count()
    
    board.turn = chess.BLACK
    black_mobility = board.legal_moves.count()
    
    board.turn = current_turn
    
    score += (white_mobility - black_mobility) * 5
    
    return score
