import chess
import pyglet
from pyglet import shapes
from pyglet.text import Label
from pyglet.window import key, mouse
from pathlib import Path
import time
import search

SQUARE_SIZE = 80
BOARD_PX = SQUARE_SIZE * 8
DASHBOARD_WIDTH = 200
WINDOW_WIDTH = BOARD_PX + DASHBOARD_WIDTH
WINDOW_HEIGHT = BOARD_PX

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT = (186, 202, 68, 128)
DASHBOARD_BG = (50, 50, 50)

PIECE_IMAGES = {
    "P": "wP.png", "N": "wN.png", "B": "wB.png",
    "R": "wR.png", "Q": "wQ.png", "K": "wK.png",
    "p": "bP.png", "n": "bN.png", "b": "bB.png",
    "r": "bR.png", "q": "bQ.png", "k": "bK.png",
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
        self.legal_moves_for_selected = set()
        self.ai_thinking = False
        self.piece_textures = {}
        assets = Path(__file__).parent / "assets"
        for sym, filename in PIECE_IMAGES.items():
            self.piece_textures[sym] = pyglet.image.load(str(assets / filename))
        pyglet.clock.schedule_interval(self.update, 0.1)

    def on_draw(self):
        self.clear()
        self.draw_board()
        self.draw_pieces()
        self.draw_dashboard()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.R:
            self.board.reset()
            self.selected_square = None
            self.legal_moves_for_selected.clear()
            self.move_count = 0
            self.nodes = 0
            self.think_time = 0.0
            self.ai_thinking = False
        elif symbol == key.M:
            modes = ["pvp", "pve-white", "pve-black"]
            idx = modes.index(self.mode)
            self.mode = modes[(idx + 1) % len(modes)]
            self.board.reset()
            self.selected_square = None
            self.legal_moves_for_selected.clear()
            self.move_count = 0
            self.nodes = 0
            self.think_time = 0.0
            self.ai_thinking = False

    def on_mouse_press(self, x, y, button, modifiers):
        if self.ai_thinking:
            return
        if x >= BOARD_PX:
            return
        if self.mode == "pve-white" and self.board.turn == chess.BLACK:
            return
        if self.mode == "pve-black" and self.board.turn == chess.WHITE:
            return

        square = self.square_from_pos(x, y)
        if square is None:
            return

        piece = self.board.piece_at(square)
        if self.selected_square is None:
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.legal_moves_for_selected = {
                    m.to_square for m in self.board.legal_moves if m.from_square == square
                }
        else:
            if square in self.legal_moves_for_selected:
                move = chess.Move(self.selected_square, square)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.move_count += 1
                    self.selected_square = None
                    self.legal_moves_for_selected.clear()
                else:
                    self.selected_square = None
                    self.legal_moves_for_selected.clear()
            elif piece and piece.color == self.board.turn:
                self.selected_square = square
                self.legal_moves_for_selected = {
                    m.to_square for m in self.board.legal_moves if m.from_square == square
                }
            else:
                self.selected_square = None
                self.legal_moves_for_selected.clear()

    def update(self, dt):
        if self.board.is_game_over():
            return
        if self.ai_thinking:
            return

        if self.mode == "pve-white" and self.board.turn == chess.BLACK:
            self.ai_move()
        elif self.mode == "pve-black" and self.board.turn == chess.WHITE:
            self.ai_move()

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = (7 - row) * SQUARE_SIZE
                color = LIGHT if (row + col) % 2 == 0 else DARK
                square = chess.square(col, row)
                if square == self.selected_square:
                    rect = shapes.Rectangle(x, y, SQUARE_SIZE, SQUARE_SIZE, color=HIGHLIGHT)
                elif square in self.legal_moves_for_selected:
                    rect = shapes.Rectangle(x, y, SQUARE_SIZE, SQUARE_SIZE, color=HIGHLIGHT)
                else:
                    rect = shapes.Rectangle(x, y, SQUARE_SIZE, SQUARE_SIZE, color=color)
                rect.draw()

    def draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece is None:
                continue
            if self.selected_square == square:
                continue
            col = chess.square_file(square)
            row = chess.square_rank(square)
            x = col * SQUARE_SIZE
            y = (7 - row) * SQUARE_SIZE
            texture = self.piece_textures[piece.symbol()]
            sprite = pyglet.sprite.Sprite(texture, x=x, y=y)
            sprite.draw()

    def draw_dashboard(self):
        rect = shapes.Rectangle(BOARD_PX, 0, DASHBOARD_WIDTH, WINDOW_HEIGHT, color=DASHBOARD_BG)
        rect.draw()

        title = Label("Chess AI", font_size=18, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 20,
                      anchor_y="top", color=(255, 255, 255, 255))
        title.draw()

        mode_label = Label(f"Mode: {self.mode}", font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 50,
                           anchor_y="top", color=(200, 200, 200, 255))
        mode_label.draw()

        moves = Label(f"Moves: {self.move_count}", font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 80,
                      anchor_y="top", color=(200, 200, 200, 255))
        moves.draw()

        turn = Label(f"Turn: {'White' if self.board.turn == chess.WHITE else 'Black'}",
                     font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 110,
                     anchor_y="top", color=(200, 200, 200, 255))
        turn.draw()

        nodes_label = Label(f"Nodes: {self.nodes}", font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 140,
                            anchor_y="top", color=(200, 200, 200, 255))
        nodes_label.draw()

        time_label = Label(f"Time: {self.think_time:.2f}s", font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 170,
                           anchor_y="top", color=(200, 200, 200, 255))
        time_label.draw()

        reset_label = Label("R: Reset", font_size=11, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 210,
                            anchor_y="top", color=(150, 150, 150, 255))
        reset_label.draw()

        mode_label2 = Label("M: Change Mode", font_size=11, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 230,
                            anchor_y="top", color=(150, 150, 150, 255))
        mode_label2.draw()

        if self.board.is_game_over():
            result = Label("Game Over", font_size=16, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 270,
                           anchor_y="top", color=(255, 100, 100, 255))
            result.draw()

    def square_from_pos(self, x, y):
        col = int(x // SQUARE_SIZE)
        row = 7 - int(y // SQUARE_SIZE)
        if 0 <= col < 8 and 0 <= row < 8:
            return chess.square(col, row)
        return None

    def ai_move(self):
        self.ai_thinking = True
        start = time.time()
        move = search.get_best_move(self.board, depth=3)
        elapsed = time.time() - start
        if move:
            self.board.push(move)
            self.move_count += 1
            self.nodes = search.NODES_SEARCHED
            self.think_time = elapsed
        self.ai_thinking = False
