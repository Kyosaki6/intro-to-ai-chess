import chess
import pyglet
from pyglet import shapes
from pyglet.text import Label
from pyglet.window import key, mouse
import time
from search import get_best_move, NODES_SEARCHED

SQUARE_SIZE = 80
BOARD_PX = SQUARE_SIZE * 8
DASHBOARD_WIDTH = 200
WINDOW_WIDTH = BOARD_PX + DASHBOARD_WIDTH
WINDOW_HEIGHT = BOARD_PX

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT = (186, 202, 68, 128)
DASHBOARD_BG = (50, 50, 50)

UNICODE_PIECES = {
    "P": "\u2659", "N": "\u2658", "B": "\u2657",
    "R": "\u2656", "Q": "\u2655", "K": "\u2654",
    "p": "\u265F", "n": "\u265E", "b": "\u265D",
    "r": "\u265C", "q": "\u265B", "k": "\u265A",
}

PIECE_COLORS = {
    "P": (0, 0, 0), "N": (0, 0, 0), "B": (0, 0, 0),
    "R": (0, 0, 0), "Q": (0, 0, 0), "K": (0, 0, 0),
    "p": (50, 50, 50), "n": (50, 50, 50), "b": (50, 50, 50),
    "r": (50, 50, 50), "q": (50, 50, 50), "k": (50, 50, 50),
}


class ChessGUI(pyglet.window.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Chess AI")
        self.board = chess.Board()
        self.selected_square = None
        self.move_count = 0
        self.nodes = 0
        self.think_time = 0.0
        self.mode = "pvp"
        pyglet.clock.schedule_interval(self.update, 0.1)

    def on_draw(self):
        pass

    def on_key_press(self, symbol, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def update(self, dt):
        pass

    def draw_board(self):
        pass

    def draw_pieces(self):
        pass

    def draw_dashboard(self):
        pass

    def square_from_pos(self, x, y):
        return None

    def ai_move(self):
        pass
