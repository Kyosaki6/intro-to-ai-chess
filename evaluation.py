import chess


def evaluate_board(board: chess.Board) -> float:
    """TODO (Person 2): tính điểm bàn cờ (material + position).
    Trả về dương nếu White lợi thế, âm nếu Black lợi thế.

    Gợi ý điểm quân:
      Tốt(P)=100, Mã(N)=300, Tượng(B)=300, Xe(R)=500, Hậu(Q)=900, Vua(K)=20000

    Gợi ý: duyệt qua chess.SQUARES, lấy board.piece_at(square),
    cộng điểm quân + điểm vị trí (Piece-Square Tables).
    """
    return 0
