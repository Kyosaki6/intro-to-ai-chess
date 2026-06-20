import chess
import pyglet
from pyglet import shapes
from pyglet.text import Label
from pyglet.window import key, mouse
from pathlib import Path
import struct
import math
import wave as wav_module

SQUARE_SIZE = 80
BOARD_PX = SQUARE_SIZE * 8
DASHBOARD_WIDTH = 200
WINDOW_WIDTH = BOARD_PX + DASHBOARD_WIDTH
WINDOW_HEIGHT = BOARD_PX

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT_FILL = (0, 200, 80, 50)
HIGHLIGHT_BORDER = (0, 200, 80, 180)
CAPTURE_FILL = (200, 50, 50, 50)
CAPTURE_BORDER = (200, 50, 50, 180)
CASTLE_FILL = (200, 180, 50, 50)
CASTLE_BORDER = (200, 180, 50, 180)
CHECK_FILL = (200, 30, 30, 120)
DASHBOARD_BG = (50, 50, 50)
BORDER_OUTER = (50, 30, 15)
BORDER_INNER = (100, 70, 40)

PIECE_IMAGES = {
    "P": "wP.png", "N": "wN.png", "B": "wB.png",
    "R": "wR.png", "Q": "wQ.png", "K": "wK.png",
    "p": "bP.png", "n": "bN.png", "b": "bB.png",
    "r": "bR.png", "q": "bQ.png", "k": "bK.png",
}


def _make_wav(filename, freq, duration, vol=0.3):
    sr = 22050
    n = int(sr * duration)
    with wav_module.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        for i in range(n):
            t = i / sr
            v = int(vol * 32767 * math.sin(2 * math.pi * freq * t))
            f.writeframes(struct.pack('<h', v))


def _make_background_wav(filename, sr=22050, duration=10.0):
    n = int(sr * duration)
    freqs = [(130.81, 0.12), (164.81, 0.08), (196.00, 0.10),
             (261.63, 0.06), (329.63, 0.04), (392.00, 0.05)]
    fade = 0.3
    with wav_module.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        for i in range(n):
            t = i / sr
            env = 1.0
            if t < fade:
                env = t / fade
            elif t > duration - fade:
                env = (duration - t) / fade
            sample = sum(vol * math.sin(2 * math.pi * freq * t) for freq, vol in freqs)
            sample *= env * 0.5
            sample = max(-1, min(1, sample))
            f.writeframes(struct.pack('<h', int(sample * 32767 * 0.4)))


class ChessGUI(pyglet.window.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Chess AI")
        self.state = "menu"
        self.board = chess.Board()
        self.selected_square = None
        self.move_count = 0
        self.mode = "pvp"
        self.legal_moves_for_selected = set()
        self.promotion_pending = False
        self.promotion_from_sq = None
        self.promotion_to_sq = None
        self.promotion_moves = []
        self.menu_buttons = []
        self.piece_textures = {}
        self.dragging = False
        self.drag_x = 0
        self.drag_y = 0
        self.show_settings = False
        self.music_volume = 0.3
        self.music_player = None

        assets = Path(__file__).parent / "assets"
        for sym, filename in PIECE_IMAGES.items():
            self.piece_textures[sym] = pyglet.image.load(str(assets / filename))

        self.board_texture = pyglet.image.load(str(assets / "chess.png"))
        w, h = self.board_texture.width, self.board_texture.height
        size = min(w, h)
        ox = (w - size) // 2
        oy = (h - size) // 2
        self.board_region = self.board_texture.get_region(ox, oy, size, size)

        self.sounds_dir = Path(__file__).parent / "sounds"
        self.sounds_dir.mkdir(exist_ok=True)
        self._init_sounds()
        self._init_background_music()

        pyglet.clock.schedule_interval(self.update, 0.1)

    def _init_sounds(self):
        self.sounds = {}
        sound_files = {
            "move": ("move.wav", 600, 0.08, 0.25),
            "capture": ("capture.wav", 400, 0.12, 0.3),
            "check": ("check.wav", 880, 0.15, 0.35),
        }
        for key, (fn, freq, dur, vol) in sound_files.items():
            path = self.sounds_dir / fn
            if not path.exists():
                _make_wav(str(path), freq, dur, vol)
            try:
                self.sounds[key] = pyglet.media.load(str(path), streaming=False)
            except Exception:
                self.sounds[key] = None

    def _init_background_music(self):
        path = self.sounds_dir / "background.wav"
        if not path.exists():
            _make_background_wav(str(path))
        try:
            source = pyglet.media.load(str(path), streaming=True)
            self.music_player = pyglet.media.Player()
            self.music_player.queue(source)
            self.music_player.volume = self.music_volume * 0.5
            self.music_player.play()
        except Exception:
            self.music_player = None

    def _play_sound(self, key):
        s = self.sounds.get(key)
        if s:
            s.play()

    def _update_music_volume(self):
        if self.music_player:
            self.music_player.volume = self.music_volume * 0.5

    def on_draw(self):
        self.clear()
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_board()
            self.draw_pieces()
            self.draw_dashboard()
            if self.dragging and self.selected_square is not None:
                self._draw_dragged_piece()
            if self.promotion_pending:
                self.draw_promotion_dialog()

    def _draw_dragged_piece(self):
        piece = self.board.piece_at(self.selected_square)
        if piece is None:
            return
        texture = self.piece_textures[piece.symbol()]
        sprite = pyglet.sprite.Sprite(texture, x=self.drag_x - SQUARE_SIZE // 2,
                                      y=self.drag_y - SQUARE_SIZE // 2)
        sprite.opacity = 180
        sprite.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "menu":
            if self.show_settings:
                self._handle_settings_click(x, y)
            else:
                self._handle_menu_click(x, y)
            return

        if self.promotion_pending:
            self._handle_promotion_click(x, y)
            return

        if x >= BOARD_PX:
            self.selected_square = None
            self.legal_moves_for_selected.clear()
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
                self._execute_move(square)
            elif piece and piece.color == self.board.turn:
                if not self._try_castling_via_rook(square):
                    self.selected_square = square
                    self.legal_moves_for_selected = {
                        m.to_square for m in self.board.legal_moves if m.from_square == square
                    }
            else:
                self.selected_square = None
                self.legal_moves_for_selected.clear()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.state == "menu" and self.show_settings:
            dw, dh = 380, 260
            dialog_x = (BOARD_PX - dw) // 2
            dialog_y = (BOARD_PX - dh) // 2
            bar_x = dialog_x + 40
            bar_y = dialog_y + dh - 115
            bar_w = dw - 80
            bar_h = 16
            if bar_x <= x <= bar_x + bar_w and bar_y <= y <= bar_y + bar_h:
                self.music_volume = max(0.0, min(1.0, (x - bar_x) / bar_w))
                self._update_music_volume()
            return
        if self.state != "game":
            return
        if self.selected_square is not None:
            self.dragging = True
            self.drag_x = x
            self.drag_y = y

    def on_mouse_release(self, x, y, button, modifiers):
        if self.state != "game":
            return
        if self.dragging and self.selected_square is not None:
            if 0 <= x < BOARD_PX and 0 <= y < BOARD_PX:
                square = self.square_from_pos(x, y)
                if square is not None and square in self.legal_moves_for_selected:
                    self._execute_move(square)
                elif square is not None and self._try_castling_via_rook(square):
                    pass
                else:
                    self.selected_square = None
                    self.legal_moves_for_selected.clear()
            else:
                self.selected_square = None
                self.legal_moves_for_selected.clear()
        self.dragging = False

    def _try_castling_via_rook(self, rook_sq):
        if self.selected_square is None:
            return False
        king_pt = self.board.piece_at(self.selected_square)
        rook_pt = self.board.piece_at(rook_sq)
        if king_pt is None or king_pt.piece_type != chess.KING:
            return False
        if rook_pt is None or rook_pt.piece_type != chess.ROOK or rook_pt.color != king_pt.color:
            return False
        if rook_sq == chess.H1:
            target = chess.G1
        elif rook_sq == chess.A1:
            target = chess.C1
        elif rook_sq == chess.H8:
            target = chess.G8
        elif rook_sq == chess.A8:
            target = chess.C8
        else:
            return False
        for m in self.board.legal_moves:
            if m.from_square == self.selected_square and m.to_square == target and self.board.is_castling(m):
                self._execute_move(target)
                return True
        return False

    def _execute_move(self, target_sq):
        moves = [m for m in self.board.legal_moves
                 if m.from_square == self.selected_square and m.to_square == target_sq]
        if not moves:
            self.selected_square = None
            self.legal_moves_for_selected.clear()
            return

        if moves[0].promotion:
            self.promotion_pending = True
            self.promotion_from_sq = self.selected_square
            self.promotion_to_sq = target_sq
            self.promotion_moves = moves
            return

        captured = self.board.piece_at(target_sq) is not None
        self.board.push(moves[0])
        self.move_count += 1
        self.selected_square = None
        self.legal_moves_for_selected.clear()

        if self.board.is_check():
            self._play_sound("check")
        elif captured:
            self._play_sound("capture")
        else:
            self._play_sound("move")

    def _clear_promotion(self):
        self.promotion_pending = False
        self.promotion_from_sq = None
        self.promotion_to_sq = None
        self.promotion_moves = []

    def draw_menu(self):
        shapes.Rectangle(0, 0, BOARD_PX, BOARD_PX, color=(30, 30, 30)).draw()

        cx = BOARD_PX // 2
        title = Label("CHESS AI", font_size=42,
                      x=cx, y=BOARD_PX - 80,
                      anchor_x="center", anchor_y="center",
                      color=(240, 217, 181, 255))
        title.draw()

        subtitle = Label("Trí tuệ nhân tạo - Cờ Vua", font_size=16,
                         x=cx, y=BOARD_PX - 130,
                         anchor_x="center", anchor_y="center",
                         color=(180, 180, 180, 255))
        subtitle.draw()

        btn_w, btn_h = 260, 55
        btn_y_start = BOARD_PX // 2 + 40
        self.menu_buttons = []

        button_data = [
            ("2 Người Chơi", "pvp"),
            ("⚙ Cài Đặt", "settings"),
        ]

        for i, (text, mode) in enumerate(button_data):
            bx = cx - btn_w // 2
            by = btn_y_start - i * (btn_h + 15)
            self.menu_buttons.append({"rect": (bx, by, btn_w, btn_h), "mode": mode})
            shapes.BorderedRectangle(bx, by, btn_w, btn_h,
                                     border=2,
                                     color=(60, 60, 60, 200),
                                     border_color=(180, 140, 100, 200)).draw()
            Label(text, font_size=18,
                  x=cx, y=by + btn_h // 2,
                  anchor_x="center", anchor_y="center",
                  color=(255, 255, 255, 255)).draw()



        shapes.Rectangle(BOARD_PX, 0, DASHBOARD_WIDTH, WINDOW_HEIGHT, color=DASHBOARD_BG).draw()
        Label("Chess AI", font_size=18, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 20,
              anchor_y="top", color=(255, 255, 255, 255)).draw()
        Label("Chọn chế độ để bắt đầu", font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 50,
              anchor_y="top", color=(120, 120, 120, 255)).draw()

        if self.show_settings:
            self._draw_settings_dialog()

    def _draw_settings_dialog(self):
        overlay = shapes.Rectangle(0, 0, BOARD_PX, BOARD_PX, color=(0, 0, 0, 160))
        overlay.draw()

        dw, dh = 380, 260
        dx = (BOARD_PX - dw) // 2
        dy = (BOARD_PX - dh) // 2

        shapes.Rectangle(dx, dy, dw, dh, color=(40, 40, 40, 240)).draw()
        shapes.BorderedRectangle(dx, dy, dw, dh, border=2,
                                 color=(40, 40, 40, 240),
                                 border_color=(180, 140, 100, 200)).draw()

        cx = BOARD_PX // 2
        title = Label("Cài Đặt Âm Thanh", font_size=18,
                      x=cx, y=dy + dh - 30,
                      anchor_x="center", anchor_y="center",
                      color=(255, 255, 255, 255))
        title.draw()

        vol_label = Label(f"Nhạc nền: {int(self.music_volume * 100)}%",
                          font_size=14,
                          x=cx, y=dy + dh - 75,
                          anchor_x="center", anchor_y="center",
                          color=(200, 200, 200, 255))
        vol_label.draw()

        bar_x = dx + 40
        bar_y = dy + dh - 115
        bar_w = dw - 80
        bar_h = 16

        shapes.Rectangle(bar_x, bar_y, bar_w, bar_h, color=(80, 80, 80, 200)).draw()
        fill_w = int(bar_w * self.music_volume)
        if fill_w > 0:
            shapes.Rectangle(bar_x, bar_y, fill_w, bar_h, color=(100, 180, 80, 200)).draw()
        shapes.BorderedRectangle(bar_x, bar_y, bar_w, bar_h, border=1,
                                 color=(80, 80, 80, 200),
                                 border_color=(180, 140, 100, 180)).draw()

        pct = Label(f"0%{' ' * 20}100%", font_size=9,
                    x=cx, y=bar_y - 15,
                    anchor_x="center", anchor_y="center",
                    color=(140, 140, 140, 255))
        pct.draw()

        # Volume presets
        preset_y = bar_y - 50
        preset_x_start = dx + 30
        presets = [("0%", 0), ("25%", 0.25), ("50%", 0.5), ("75%", 0.75), ("100%", 1.0)]
        self.settings_buttons = []
        for j, (label, val) in enumerate(presets):
            px = preset_x_start + j * 65
            pw, ph = 55, 28
            self.settings_buttons.append({"rect": (px, preset_y, pw, ph), "action": "volume", "value": val})
            clr = (100, 180, 80, 200) if abs(self.music_volume - val) < 0.01 else (70, 70, 70, 200)
            shapes.BorderedRectangle(px, preset_y, pw, ph, border=1,
                                     color=clr,
                                     border_color=(150, 150, 150, 200)).draw()
            Label(label, font_size=11,
                  x=px + pw // 2, y=preset_y + ph // 2,
                  anchor_x="center", anchor_y="center",
                  color=(255, 255, 255, 255)).draw()

        close_y = dy + 15
        close_w, close_h = 80, 30
        cx_btn = dx + dw // 2
        self.settings_buttons.append({"rect": (cx_btn - close_w // 2, close_y, close_w, close_h),
                                       "action": "close", "value": None})
        shapes.BorderedRectangle(cx_btn - close_w // 2, close_y, close_w, close_h,
                                 border=1,
                                 color=(80, 50, 50, 200),
                                 border_color=(200, 100, 100, 200)).draw()
        Label("✕ Đóng", font_size=12,
              x=cx_btn, y=close_y + close_h // 2,
              anchor_x="center", anchor_y="center",
              color=(255, 200, 200, 255)).draw()

    def _handle_menu_click(self, x, y):
        for btn in self.menu_buttons:
            bx, by, bw, bh = btn["rect"]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if btn["mode"] == "settings":
                    self.show_settings = True
                else:
                    self.mode = btn["mode"]
                    self.board.reset()
                    self.selected_square = None
                    self.legal_moves_for_selected.clear()
                    self.move_count = 0
                    self._clear_promotion()
                    self.state = "game"
                return

    def _handle_settings_click(self, x, y):
        for btn in self.settings_buttons:
            bx, by, bw, bh = btn["rect"]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if btn["action"] == "close":
                    self.show_settings = False
                elif btn["action"] == "volume":
                    self.music_volume = btn["value"]
                    self._update_music_volume()
                return
        # Click on volume bar
        dw, dh = 380, 260
        dx = (BOARD_PX - dw) // 2
        dy = (BOARD_PX - dh) // 2
        bar_x = dx + 40
        bar_y = dy + dh - 115
        bar_w = dw - 80
        bar_h = 16
        if bar_x <= x <= bar_x + bar_w and bar_y <= y <= bar_y + bar_h:
            self.music_volume = max(0.0, min(1.0, (x - bar_x) / bar_w))
            self._update_music_volume()

    def on_key_press(self, symbol, modifiers):
        if self.state == "menu":
            if self.show_settings:
                if symbol == key.ESCAPE:
                    self.show_settings = False
                return
            return
        if symbol == key.ESCAPE:
            self.show_settings = False
            self.state = "menu"
            self.board.reset()
            self.selected_square = None
            self.legal_moves_for_selected.clear()
            self.move_count = 0
            self._clear_promotion()
        elif symbol == key.R:
            self.board.reset()
            self.selected_square = None
            self.legal_moves_for_selected.clear()
            self.move_count = 0
            self._clear_promotion()

    def update(self, dt):
        if self.state == "menu":
            return
        if self.board.is_game_over():
            return

    def draw_board(self):
        shapes.Rectangle(-8, -8, BOARD_PX + 16, BOARD_PX + 16, color=BORDER_OUTER).draw()
        shapes.Rectangle(-4, -4, BOARD_PX + 8, BOARD_PX + 8, color=BORDER_INNER).draw()
        scale = BOARD_PX / self.board_region.width
        sprite = pyglet.sprite.Sprite(self.board_region)
        sprite.scale = scale
        sprite.draw()

        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                kx = chess.square_file(king_sq) * SQUARE_SIZE
                ky = chess.square_rank(king_sq) * SQUARE_SIZE
                shapes.Rectangle(kx, ky, SQUARE_SIZE, SQUARE_SIZE, color=CHECK_FILL).draw()

        for square in chess.SQUARES:
            col = chess.square_file(square)
            row = chess.square_rank(square)
            x = col * SQUARE_SIZE
            y = row * SQUARE_SIZE
            if square == self.selected_square:
                shapes.Rectangle(x, y, SQUARE_SIZE, SQUARE_SIZE, color=HIGHLIGHT_FILL).draw()
                self._draw_square_border(x, y, HIGHLIGHT_BORDER)
            elif square in self.legal_moves_for_selected:
                target = self.board.piece_at(square)
                if target:
                    shapes.Rectangle(x, y, SQUARE_SIZE, SQUARE_SIZE, color=CAPTURE_FILL).draw()
                    self._draw_square_border(x, y, CAPTURE_BORDER)
                else:
                    shapes.Rectangle(x, y, SQUARE_SIZE, SQUARE_SIZE, color=HIGHLIGHT_FILL).draw()
                    self._draw_square_border(x, y, HIGHLIGHT_BORDER)

        if self.selected_square is not None:
            piece = self.board.piece_at(self.selected_square)
            if piece and piece.piece_type == chess.KING:
                for m in self.board.legal_moves:
                    if m.from_square == self.selected_square and self.board.is_castling(m):
                        if m.to_square == chess.G1 or m.to_square == chess.G8:
                            rook_sq = chess.H1 if m.to_square == chess.G1 else chess.H8
                        elif m.to_square == chess.C1 or m.to_square == chess.C8:
                            rook_sq = chess.A1 if m.to_square == chess.C1 else chess.A8
                        else:
                            continue
                        rx = chess.square_file(rook_sq) * SQUARE_SIZE
                        ry = chess.square_rank(rook_sq) * SQUARE_SIZE
                        shapes.Rectangle(rx, ry, SQUARE_SIZE, SQUARE_SIZE, color=CASTLE_FILL).draw()
                        self._draw_square_border(rx, ry, CASTLE_BORDER)

        files = "abcdefgh"
        for col in range(8):
            Label(files[col], font_size=12,
                  x=col * SQUARE_SIZE + SQUARE_SIZE // 2,
                  y=4, anchor_x="center", anchor_y="bottom",
                  color=(0, 0, 0, 100)).draw()
            Label(files[col], font_size=12,
                  x=col * SQUARE_SIZE + SQUARE_SIZE // 2,
                  y=BOARD_PX - 4, anchor_x="center", anchor_y="top",
                  color=(0, 0, 0, 100)).draw()

        for row in range(8):
            Label(str(row + 1), font_size=12,
                  x=4, y=row * SQUARE_SIZE + SQUARE_SIZE // 2,
                  anchor_x="left", anchor_y="center",
                  color=(0, 0, 0, 100)).draw()
            Label(str(row + 1), font_size=12,
                  x=BOARD_PX - 4, y=row * SQUARE_SIZE + SQUARE_SIZE // 2,
                  anchor_x="right", anchor_y="center",
                  color=(0, 0, 0, 100)).draw()

    def _draw_square_border(self, x, y, color):
        b = 3
        shapes.Rectangle(x, y, SQUARE_SIZE, b, color=color).draw()
        shapes.Rectangle(x, y + SQUARE_SIZE - b, SQUARE_SIZE, b, color=color).draw()
        shapes.Rectangle(x, y, b, SQUARE_SIZE, color=color).draw()
        shapes.Rectangle(x + SQUARE_SIZE - b, y, b, SQUARE_SIZE, color=color).draw()

    def draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece is None:
                continue
            if self.selected_square == square:
                if self.dragging:
                    continue
                sprite = pyglet.sprite.Sprite(self.piece_textures[piece.symbol()],
                                              x=chess.square_file(square) * SQUARE_SIZE,
                                              y=chess.square_rank(square) * SQUARE_SIZE)
                sprite.opacity = 100
                sprite.draw()
            else:
                col = chess.square_file(square)
                row = chess.square_rank(square)
                texture = self.piece_textures[piece.symbol()]
                sprite = pyglet.sprite.Sprite(texture, x=col * SQUARE_SIZE, y=row * SQUARE_SIZE)
                sprite.draw()

    def draw_dashboard(self):
        rect = shapes.Rectangle(BOARD_PX, 0, DASHBOARD_WIDTH, WINDOW_HEIGHT, color=DASHBOARD_BG)
        rect.draw()

        title = Label("Chess AI", font_size=18, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 20,
                      anchor_y="top", color=(255, 255, 255, 255))
        title.draw()

        mode_label = Label("Mode: PvP", font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 50,
                           anchor_y="top", color=(200, 200, 200, 255))
        mode_label.draw()

        moves = Label(f"Moves: {self.move_count}", font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 80,
                      anchor_y="top", color=(200, 200, 200, 255))
        moves.draw()

        turn = Label(f"Turn: {'White' if self.board.turn == chess.WHITE else 'Black'}",
                     font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 110,
                     anchor_y="top", color=(200, 200, 200, 255))
        turn.draw()

        vol_label = Label(f"Music: {int(self.music_volume * 100)}%",
                          font_size=12, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 140,
                          anchor_y="top", color=(200, 200, 200, 255))
        vol_label.draw()

        reset_label = Label("R: Reset  |  ESC: Menu", font_size=11, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 170,
                            anchor_y="top", color=(150, 150, 150, 255))
        reset_label.draw()

        if self.board.is_game_over():
            result = Label("Game Over", font_size=16, x=BOARD_PX + 10, y=WINDOW_HEIGHT - 210,
                           anchor_y="top", color=(255, 100, 100, 255))
            result.draw()

    def draw_promotion_dialog(self):
        overlay = shapes.Rectangle(0, 0, BOARD_PX, BOARD_PX, color=(0, 0, 0, 150))
        overlay.draw()

        pieces = ["Q", "R", "B", "N"]
        labels = ["Hậu", "Xe", "Tượng", "Mã"]
        dialog_y = BOARD_PX // 2 - SQUARE_SIZE // 2
        dialog_x = BOARD_PX // 2 - 2 * SQUARE_SIZE

        bg = shapes.Rectangle(dialog_x - 10, dialog_y - 10,
                               4 * SQUARE_SIZE + 20, SQUARE_SIZE + 60,
                               color=(30, 30, 30, 230))
        bg.draw()

        title = Label("Phong cấp - Chọn quân:", font_size=14,
                      x=BOARD_PX // 2, y=dialog_y + SQUARE_SIZE + 25,
                      anchor_x="center", anchor_y="center",
                      color=(255, 255, 255, 255))
        title.draw()

        is_white = self.board.turn == chess.WHITE
        for i, sym in enumerate(pieces):
            px = dialog_x + i * SQUARE_SIZE
            py = dialog_y
            box = shapes.BorderedRectangle(px, py, SQUARE_SIZE, SQUARE_SIZE,
                                           color=(60, 60, 60, 200),
                                           border_color=(200, 200, 200, 200),
                                           border=2)
            box.draw()
            key = sym if is_white else sym.lower()
            texture = self.piece_textures[key]
            sprite = pyglet.sprite.Sprite(texture, x=px, y=py)
            sprite.draw()
            name_label = Label(labels[i], font_size=10,
                               x=px + SQUARE_SIZE // 2, y=py - 12,
                               anchor_x="center", anchor_y="center",
                               color=(200, 200, 200, 255))
            name_label.draw()

        hint = Label("Click vào quân muốn phong cấp", font_size=11,
                     x=BOARD_PX // 2, y=dialog_y - 35,
                     anchor_x="center", anchor_y="center",
                     color=(180, 180, 180, 255))
        hint.draw()

    def _handle_promotion_click(self, x, y):
        sym = self._promotion_sym_at_pos(x, y)
        if sym is None:
            return
        promo_map = {"Q": chess.QUEEN, "R": chess.ROOK, "B": chess.BISHOP, "N": chess.KNIGHT}
        promo = promo_map.get(sym)
        if promo is None:
            return
        for m in self.promotion_moves:
            if m.promotion == promo:
                self.board.push(m)
                self.move_count += 1
                if self.board.is_check():
                    self._play_sound("check")
                else:
                    self._play_sound("move")
                break
        self._clear_promotion()

    def _promotion_sym_at_pos(self, x, y):
        pieces = ["Q", "R", "B", "N"]
        dialog_y = BOARD_PX // 2 - SQUARE_SIZE // 2
        dialog_x = BOARD_PX // 2 - 2 * SQUARE_SIZE
        for i, sym in enumerate(pieces):
            px = dialog_x + i * SQUARE_SIZE
            py = dialog_y
            if px <= x <= px + SQUARE_SIZE and py <= y <= py + SQUARE_SIZE:
                return sym
        return None

    def square_from_pos(self, x, y):
        col = int(x // SQUARE_SIZE)
        row = int(y // SQUARE_SIZE)
        if 0 <= col < 8 and 0 <= row < 8:
            return chess.square(col, row)
        return None
