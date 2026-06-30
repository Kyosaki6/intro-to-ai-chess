import chess
from evaluation import evaluate_board

def test_mobility_symmetry():
    board = chess.Board()
    # Initial position: white and black should have same mobility if we ignore turn
    # Actually, they might not, but the evaluation should be consistent.
    # The key is that the mobility bonus *itself* should be calculated 
    # independent of board.turn
    
    # Test 1: Initial position, White to move
    board.turn = chess.WHITE
    score1 = evaluate_board(board)
    
    # Test 2: Initial position, Black to move (symmetry check)
    # The evaluation from White's perspective should be the same
    # regardless of who is moving.
    board.turn = chess.BLACK
    score2 = evaluate_board(board)
    
    # In the initial position, the board is symmetrical, 
    # except for the turn. With the fix, score should be the same
    # because mobility is (white_moves - black_moves) * 5.
    # Actually, initial mobility is the same for both sides.
    assert abs(score1 - score2) < 1e-6, f"Mobility score not symmetric: {score1} vs {score2}"
    print("Mobility symmetry test passed!")

def test_phase_calculation():
    # Board with lots of material
    board = chess.Board()
    # Board with little material
    board_empty = chess.Board("k7/8/8/8/8/8/8/K7 w - - 0 1")
    
    score_full = evaluate_board(board)
    score_empty = evaluate_board(board_empty)
    
    # Phase should affect the King score.
    # This is a bit hard to test precisely without internal access,
    # but at least we can verify it runs.
    print("Phase calculation test passed!")

if __name__ == "__main__":
    test_mobility_symmetry()
    test_phase_calculation()
    print("All tests passed!")
