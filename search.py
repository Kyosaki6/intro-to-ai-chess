import chess
from evaluation import evaluate_board

NODES_SEARCHED = 0


def get_best_move(board: chess.Board, depth: int = 3) -> chess.Move | None:
    """TODO (Person 1): tìm nước đi tốt nhất bằng Minimax + Alpha-Beta.

    1. Reset NODES_SEARCHED = 0.
    2. Duyệt board.legal_moves.
    3. Với mỗi move: board.push(), đệ quy minimax(), board.pop().
    4. Chọn move có score cao nhất (White = max) / thấp nhất (Black = min).
    5. Trả về best_move.
    """
    return None


def minimax(board: chess.Board, depth: int, alpha: float, beta: float,
            is_maximizing: bool) -> float:
    """TODO (Person 1): đệ quy Minimax với Alpha-Beta pruning.

    Base case: depth == 0 hoặc board.is_game_over() → evaluate_board(board).

    Nếu is_maximizing: tìm max score, ngược lại tìm min score.
    Cập nhật alpha/beta, cắt tỉa khi beta <= alpha.
    Tăng NODES_SEARCHED mỗi khi gọi đệ quy.
    """
    return 0
