import chess
import math
import pyglet
from pyglet import shapes
from pyglet.text import Label
from pyglet.window import key, mouse
from pathlib import Path

import threading

from . import constants as C
from . import audio
from search import get_best_move


class ChessGUI(pyglet.window.Window):
    def __init__(self):
        super().__init__(C.WINDOW_WIDTH, C.WINDOW_HEIGHT, "Chess AI")
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
        self.time_white = 600.0
        self.time_black = 600.0
        self.clock_running = False
        self.draw_offered_by = None
        self.game_result = None
        self.game_buttons = []
        self.ai_color = chess.BLACK
        self.use_opening_book = True
        self.ai_thinking = False
        self.last_move_square = None
        self.last_move_from_sq = None
        self.victory_text = None
        self.victory_time = 0.0
        self.redo_stack = []
        self.game_time = 600
        self.editor_palette_piece = None
        self.editor_selected_sq = None

        assets = Path(__file__).parent.parent / "assets"
        for sym, filename in C.PIECE_IMAGES.items():
            self.piece_textures[sym] = pyglet.image.load(str(assets / filename))

        self.board_texture = pyglet.image.load(str(assets / "chess.png"))
        w, h = self.board_texture.width, self.board_texture.height
        size = min(w, h)
        ox = (w - size) // 2
        oy = (h - size) // 2
        self.board_region = self.board_texture.get_region(ox, oy, size, size)

        self.sounds_dir = Path(__file__).parent.parent / "sounds"
        self.sounds_dir.mkdir(exist_ok=True)
        self._init_sounds()
        self._init_background_music()

        pyglet.clock.schedule_interval(self.update, 0.1)

    def _init_sounds(self):
        self.sounds = {}
        sound_files = {
            "move": ("move.mp3", 600, 0.08, 0.25),
            "capture": ("anquan.mp3", 400, 0.12, 0.3),
            "check": ("chieu.mp3", 880, 0.15, 0.35),
        }
        for key, (fn, freq, dur, vol) in sound_files.items():
            path = self.sounds_dir / fn
            if not path.exists():
                audio.make_wav(str(path), freq, dur, vol)
            try:
                self.sounds[key] = pyglet.media.load(str(path), streaming=False)
            except Exception:
                self.sounds[key] = None

    def _init_background_music(self):
        path = self.sounds_dir / "background.wav"
        if not path.exists():
            audio.make_background_wav(str(path))
        try:
            source = pyglet.media.load(str(path), streaming=True)
            self.music_player = pyglet.media.Player()
            self.music_player.loop = True
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
        elif self.state == "editor":
            self.draw_board()
            self.draw_pieces()
            self.draw_editor()
            if self.dragging and self.editor_palette_piece is not None:
                self._draw_editor_dragged_piece()
        else:
            self.draw_board()
            self.draw_pieces()
            self.draw_dashboard()
            if self.dragging and self.selected_square is not None:
                self._draw_dragged_piece()
            if self.promotion_pending:
                self.draw_promotion_dialog()
            if self.victory_text is not None:
                self._draw_victory_overlay()

    def _draw_dragged_piece(self):
        piece = self.board.piece_at(self.selected_square)
        if piece is None:
            return
        texture = self.piece_textures[piece.symbol()]
        sprite = pyglet.sprite.Sprite(texture, x=self.drag_x - C.SQUARE_SIZE // 2,
                                      y=self.drag_y - C.SQUARE_SIZE // 2)
        sprite.opacity = 180
        sprite.draw()

    def _draw_editor_dragged_piece(self):
        if self.editor_palette_piece is None:
            return
        if self.editor_palette_piece == "__delete__":
            cx = self.drag_x - C.SQUARE_SIZE // 2
            cy = self.drag_y - C.SQUARE_SIZE // 2
            shapes.Rectangle(cx, cy, C.SQUARE_SIZE, C.SQUARE_SIZE,
                             color=(200, 60, 60, 120)).draw()
            shapes.BorderedRectangle(cx, cy, C.SQUARE_SIZE, C.SQUARE_SIZE,
                                     border=2,
                                     color=(200, 60, 60, 120),
                                     border_color=(255, 100, 100, 120)).draw()
            Label("🗑", font_size=36,
                  x=self.drag_x, y=self.drag_y,
                  anchor_x="center", anchor_y="center",
                  color=(255, 255, 255, 200)).draw()
            return
        texture = self.piece_textures[self.editor_palette_piece]
        sprite = pyglet.sprite.Sprite(texture, x=self.drag_x - C.SQUARE_SIZE // 2,
                                      y=self.drag_y - C.SQUARE_SIZE // 2)
        sprite.opacity = 180
        sprite.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "menu":
            if self.show_settings:
                self._handle_settings_click(x, y)
            else:
                self._handle_menu_click(x, y)
            return

        if self.state == "editor":
            self._handle_editor_click(x, y, button)
            return

        if self.promotion_pending:
            self._handle_promotion_click(x, y)
            return

        if x >= C.BOARD_PX:
            self.selected_square = None
            self.legal_moves_for_selected.clear()
            for btn in self.game_buttons:
                bx, by, bw, bh = btn["rect"]
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    self._handle_game_button(btn["action"])
                    return
            return

        if self.board.is_game_over() or not self.clock_running or self.time_white <= 0 or self.time_black <= 0:
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
        if self.state == "editor":
            if self.editor_palette_piece is not None:
                self.dragging = True
                self.drag_x = x
                self.drag_y = y
            return
        if self.state == "menu" and self.show_settings:
            dw, dh = 380, 260
            dialog_x = (C.BOARD_PX - dw) // 2
            dialog_y = (C.BOARD_PX - dh) // 2
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
        if self.board.is_game_over() or not self.clock_running or self.time_white <= 0 or self.time_black <= 0:
            return
        if self.selected_square is not None:
            self.dragging = True
            self.drag_x = x
            self.drag_y = y

    def on_mouse_release(self, x, y, button, modifiers):
        if self.state == "editor":
            if self.dragging and self.editor_palette_piece is not None:
                self._handle_editor_drop(x, y)
            self.dragging = False
            return
        if self.state != "game":
            return
        if self.board.is_game_over() or not self.clock_running or self.time_white <= 0 or self.time_black <= 0:
            self.dragging = False
            return
        if self.dragging and self.selected_square is not None:
            if 0 <= x < C.BOARD_PX and 0 <= y < C.BOARD_PX:
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
        self.last_move_from_sq = self.selected_square
        self.selected_square = None
        self.legal_moves_for_selected.clear()
        self.last_move_square = target_sq
        self.redo_stack.clear()

        if self.board.is_check():
            self._play_sound("check")
        elif captured:
            self._play_sound("capture")
        else:
            self._play_sound("move")

        if self.mode == "pva" and not self.board.is_game_over() and not self.ai_thinking:
            self.ai_thinking = True
            pyglet.clock.schedule_once(lambda dt: self._do_ai_move(), 0.1)

    def _clear_promotion(self):
        self.promotion_pending = False
        self.promotion_from_sq = None
        self.promotion_to_sq = None
        self.promotion_moves = []

    def _do_ai_move(self):
        if self.board.is_game_over():
            self.ai_thinking = False
            return

        def search_thread(board_copy):
            move = get_best_move(board_copy, depth=3, use_opening_book=self.use_opening_book)
            pyglet.clock.schedule_once(lambda dt: self._apply_ai_move(move), 0)

        threading.Thread(target=search_thread, args=(self.board.copy(),), daemon=True).start()

    def _apply_ai_move(self, move):
        self.ai_thinking = False
        if move is None:
            return
        captured = self.board.piece_at(move.to_square) is not None
        self.board.push(move)
        self.move_count += 1
        self.selected_square = None
        self.legal_moves_for_selected.clear()
        self.last_move_square = move.to_square
        self.last_move_from_sq = move.from_square
        if self.board.is_check():
            self._play_sound("check")
        elif captured:
            self._play_sound("capture")
        else:
            self._play_sound("move")

    def draw_menu(self):
        shapes.Rectangle(0, 0, C.BOARD_PX, C.BOARD_PX, color=(30, 30, 30)).draw()

        cx = C.BOARD_PX // 2
        title = Label("CHESS AI", font_size=42,
                      x=cx, y=C.BOARD_PX - 80,
                      anchor_x="center", anchor_y="center",
                      color=(240, 217, 181, 255))
        title.draw()

        subtitle = Label("Trí tuệ nhân tạo - Cờ Vua", font_size=16,
                         x=cx, y=C.BOARD_PX - 130,
                         anchor_x="center", anchor_y="center",
                         color=(180, 180, 180, 255))
        subtitle.draw()

        btn_w, btn_h = 260, 55
        btn_y_start = C.BOARD_PX // 2 + 40
        self.menu_buttons = []

        button_data = [
            ("2 Người Chơi", "pvp"),
            ("🤖 Đấu với Máy", "pva"),
            ("✏ Board Editor", "editor"),
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



        shapes.Rectangle(C.BOARD_PX, 0, C.DASHBOARD_WIDTH, C.WINDOW_HEIGHT, color=C.DASHBOARD_BG).draw()
        Label("Chess AI", font_size=18, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 20,
              anchor_y="top", color=(255, 255, 255, 255)).draw()
        Label("Chọn chế độ để bắt đầu", font_size=12, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 50,
              anchor_y="top", color=(120, 120, 120, 255)).draw()

        if self.show_settings:
            self._draw_settings_dialog()

    def _draw_settings_dialog(self):
        overlay = shapes.Rectangle(0, 0, C.BOARD_PX, C.BOARD_PX, color=(0, 0, 0, 160))
        overlay.draw()

        dw, dh = 380, 260
        dx = (C.BOARD_PX - dw) // 2
        dy = (C.BOARD_PX - dh) // 2

        shapes.Rectangle(dx, dy, dw, dh, color=(40, 40, 40, 240)).draw()
        shapes.BorderedRectangle(dx, dy, dw, dh, border=2,
                                 color=(40, 40, 40, 200),
                                 border_color=(180, 140, 100, 200)).draw()

        cx = C.BOARD_PX // 2
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
                                 border_color=(180, 140, 100, 200)).draw()

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

        book_y = preset_y - 55
        book_label = Label("Khai cuộc (Book):", font_size=13,
                           x=cx - 60, y=book_y,
                           anchor_x="center", anchor_y="center",
                           color=(200, 200, 200, 255))
        book_label.draw()

        book_toggle_text = "Bật" if self.use_opening_book else "Tắt"
        book_toggle_color = (70, 130, 70, 200) if self.use_opening_book else (100, 70, 70, 200)
        toggle_x, toggle_y, toggle_w, toggle_h = cx + 30, book_y - 12, 60, 24
        self.settings_buttons.append({"rect": (toggle_x, toggle_y, toggle_w, toggle_h),
                                       "action": "toggle_book", "value": None})
        shapes.BorderedRectangle(toggle_x, toggle_y, toggle_w, toggle_h, border=1,
                                 color=book_toggle_color,
                                 border_color=(150, 150, 150, 200)).draw()
        Label(book_toggle_text, font_size=12,
              x=toggle_x + toggle_w // 2, y=toggle_y + toggle_h // 2,
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
                                 border_color=(180, 140, 100, 200)).draw()
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
                elif btn["mode"] == "editor":
                    self.board.clear()
                    self.selected_square = None
                    self.legal_moves_for_selected.clear()
                    self.state = "editor"
                    self.editor_palette_piece = None
                    self.editor_selected_sq = None
                else:
                    self.mode = btn["mode"]
                    self.board.reset()
                    self.selected_square = None
                    self.legal_moves_for_selected.clear()
                    self.move_count = 0
                    self._clear_promotion()
                    self.state = "game"
                    self.time_white = self.game_time
                    self.time_black = self.game_time
                    self.clock_running = True
                    self.draw_offered_by = None
                    self.game_result = None
                    self.ai_thinking = False
                    self.last_move_square = None
                    self.last_move_from_sq = None
                    self.redo_stack.clear()
                    self.victory_text = None
                    self.victory_time = 0.0
                    if self.mode == "pva" and self.board.turn == self.ai_color:
                        pyglet.clock.schedule_once(lambda dt: self._do_ai_move(), 0.1)
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
                elif btn["action"] == "toggle_book":
                    self.use_opening_book = not self.use_opening_book
                return
        # Click on volume bar
        dw, dh = 380, 260
        dx = (C.BOARD_PX - dw) // 2
        dy = (C.BOARD_PX - dh) // 2
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

        if self.state == "editor":
            if symbol == key.ESCAPE:
                self.state = "menu"
                self.editor_palette_piece = None
                self.editor_selected_sq = None
            return

        if symbol == key.ESCAPE:
            self.show_settings = False
            self.state = "menu"
            self.board.reset()
            self.selected_square = None
            self.legal_moves_for_selected.clear()
            self.move_count = 0
            self._clear_promotion()
            self.clock_running = False
            self.draw_offered_by = None
            self.game_result = None
            self.victory_text = None
            self.victory_time = 0.0
            self.last_move_square = None
            self.last_move_from_sq = None
            self.redo_stack.clear()
        elif symbol == key.R:
            self.board.reset()
            self.selected_square = None
            self.legal_moves_for_selected.clear()
            self.move_count = 0
            self._clear_promotion()
            self.time_white = self.game_time
            self.time_black = self.game_time
            self.clock_running = True
            self.draw_offered_by = None
            self.game_result = None
            self.victory_text = None
            self.victory_time = 0.0
            self.last_move_square = None
            self.last_move_from_sq = None
            self.redo_stack.clear()
        elif symbol == key.Z:
            self._undo_move()
        elif symbol == key.X:
            self._redo_move()
        elif symbol == key.GRAVE:
            presets = [60, 180, 300, 600, 1800]
            idx = presets.index(self.game_time) if self.game_time in presets else 3
            self.game_time = presets[(idx + 1) % len(presets)]

    def update(self, dt):
        dt = min(dt, 1.0)
        if self.state == "menu":
            return
        if self.board.is_game_over():
            if self.clock_running:
                self.clock_running = False
                self._determine_victory_text()
            if self.victory_text is not None:
                self.victory_time += dt
            return
        if not self.clock_running:
            if self.victory_text is not None:
                self.victory_time += dt
            return
        if self.board.turn == chess.WHITE:
            self.time_white -= dt
            if self.time_white <= 0:
                self.time_white = 0
                self.clock_running = False
                self._determine_victory_text()
        else:
            self.time_black -= dt
            if self.time_black <= 0:
                self.time_black = 0
                self.clock_running = False
                self._determine_victory_text()

    def _determine_victory_text(self):
        if self.game_result:
            raw = self.game_result
        elif self.time_white <= 0:
            raw = "Black wins (time)"
        elif self.time_black <= 0:
            raw = "White wins (time)"
        elif self.board.is_checkmate():
            raw = f"{'Black' if self.board.turn == chess.WHITE else 'White'} wins (checkmate)"
        elif self.board.is_stalemate():
            raw = "Stalemate"
        elif self.board.is_insufficient_material():
            raw = "Draw (material)"
        elif self.board.can_claim_draw():
            raw = "Draw"
        else:
            self.victory_text = None
            self.victory_time = 0.0
            return

        if "wins" in raw:
            winner = raw.split(" wins")[0]
            reason = raw.split("(")[-1].rstrip(")") if "(" in raw else ""
            lines = [f"{winner} thắng!"]
            if reason:
                lines.append(reason.capitalize())
            self.victory_text = "\n".join(lines)
        elif "Draw" in raw or "draw" in raw:
            self.victory_text = "Hòa cờ!"
        else:
            self.victory_text = raw
        self.victory_time = 0.0

    def _draw_victory_overlay(self):
        shapes.Rectangle(0, 0, C.BOARD_PX, C.BOARD_PX, color=(0, 0, 0, 120)).draw()

        cx = C.BOARD_PX // 2
        cy = C.BOARD_PX // 2

        pulse = 1.0 + 0.04 * math.sin(self.victory_time * 3.0)
        font_size = int(42 * pulse)
        t = self.victory_time
        r = int(220 + 35 * math.sin(t * 2.0))
        g = int(180 + 40 * math.sin(t * 2.5))
        b = int(80 + 50 * math.sin(t * 3.0))

        body = Label(
            self.victory_text,
            font_size=font_size,
            x=cx, y=cy + 20,
            anchor_x="center", anchor_y="center",
            color=(r, g, b, 255),
            multiline=True,
            width=C.BOARD_PX - 40,
            align="center",
        )
        body.draw()

        sub = Label(
            "ESC về menu  |  R: chơi lại",
            font_size=14,
            x=cx, y=cy - 50,
            anchor_x="center", anchor_y="center",
            color=(200, 200, 200, 200),
        )
        sub.draw()

    def _undo_move(self):
        if not self.board.move_stack or self.ai_thinking:
            return
        if self.promotion_pending:
            self._clear_promotion()

        self.game_result = None
        self.victory_text = None
        self.clock_running = True

        m = self.board.pop()
        self.redo_stack.append(m)
        if self.mode == "pva" and self.board.move_stack:
            m = self.board.pop()
            self.redo_stack.append(m)
        self.move_count = len(self.board.move_stack)

        self.selected_square = None
        self.legal_moves_for_selected.clear()

        if self.board.move_stack:
            prev = self.board.move_stack[-1]
            self.last_move_square = prev.to_square
            self.last_move_from_sq = prev.from_square
        else:
            self.last_move_square = None
            self.last_move_from_sq = None

    def _redo_move(self):
        if not self.redo_stack:
            return

        m = self.redo_stack.pop()
        self.board.push(m)
        self.last_move_square = m.to_square
        self.last_move_from_sq = m.from_square

        if self.mode == "pva" and self.redo_stack:
            m2 = self.redo_stack.pop()
            self.board.push(m2)
            self.last_move_square = m2.to_square
            self.last_move_from_sq = m2.from_square

        self.move_count = len(self.board.move_stack)
        self.selected_square = None
        self.legal_moves_for_selected.clear()

    def draw_board(self):
        shapes.Rectangle(-8, -8, C.BOARD_PX + 16, C.BOARD_PX + 16, color=C.BORDER_OUTER).draw()
        shapes.Rectangle(-4, -4, C.BOARD_PX + 8, C.BOARD_PX + 8, color=C.BORDER_INNER).draw()
        scale = C.BOARD_PX / self.board_region.width
        sprite = pyglet.sprite.Sprite(self.board_region)
        sprite.scale = scale
        sprite.draw()

        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                kx = chess.square_file(king_sq) * C.SQUARE_SIZE
                ky = chess.square_rank(king_sq) * C.SQUARE_SIZE
                shapes.Rectangle(kx, ky, C.SQUARE_SIZE, C.SQUARE_SIZE, color=C.CHECK_FILL).draw()

        if self.last_move_square is not None and self.last_move_square != self.selected_square:
            lx = chess.square_file(self.last_move_square) * C.SQUARE_SIZE
            ly = chess.square_rank(self.last_move_square) * C.SQUARE_SIZE
            shapes.Rectangle(lx, ly, C.SQUARE_SIZE, C.SQUARE_SIZE, color=C.LAST_MOVE_FILL).draw()
            self._draw_square_border(lx, ly, C.LAST_MOVE_BORDER)

        if self.last_move_from_sq is not None and self.last_move_from_sq != self.selected_square:
            fx = chess.square_file(self.last_move_from_sq) * C.SQUARE_SIZE
            fy = chess.square_rank(self.last_move_from_sq) * C.SQUARE_SIZE
            shapes.Rectangle(fx, fy, C.SQUARE_SIZE, C.SQUARE_SIZE, color=C.LAST_MOVE_FILL).draw()
            self._draw_square_border(fx, fy, C.LAST_MOVE_BORDER)

        for square in chess.SQUARES:
            col = chess.square_file(square)
            row = chess.square_rank(square)
            x = col * C.SQUARE_SIZE
            y = row * C.SQUARE_SIZE
            if square == self.selected_square:
                shapes.Rectangle(x, y, C.SQUARE_SIZE, C.SQUARE_SIZE, color=C.HIGHLIGHT_FILL).draw()
                self._draw_square_border(x, y, C.HIGHLIGHT_BORDER)
            elif square in self.legal_moves_for_selected:
                target = self.board.piece_at(square)
                if target:
                    shapes.Rectangle(x, y, C.SQUARE_SIZE, C.SQUARE_SIZE, color=C.CAPTURE_FILL).draw()
                    self._draw_square_border(x, y, C.CAPTURE_BORDER)
                else:
                    shapes.Rectangle(x, y, C.SQUARE_SIZE, C.SQUARE_SIZE, color=C.HIGHLIGHT_FILL).draw()
                    self._draw_square_border(x, y, C.HIGHLIGHT_BORDER)

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
                        rx = chess.square_file(rook_sq) * C.SQUARE_SIZE
                        ry = chess.square_rank(rook_sq) * C.SQUARE_SIZE
                        shapes.Rectangle(rx, ry, C.SQUARE_SIZE, C.SQUARE_SIZE, color=C.CASTLE_FILL).draw()
                        self._draw_square_border(rx, ry, C.CASTLE_BORDER)

        files = "abcdefgh"
        for col in range(8):
            Label(files[col], font_size=12,
                  x=col * C.SQUARE_SIZE + C.SQUARE_SIZE // 2,
                  y=4, anchor_x="center", anchor_y="bottom",
                  color=(0, 0, 0, 100)).draw()
            Label(files[col], font_size=12,
                  x=col * C.SQUARE_SIZE + C.SQUARE_SIZE // 2,
                  y=C.BOARD_PX - 4, anchor_x="center", anchor_y="top",
                  color=(0, 0, 0, 100)).draw()

        for row in range(8):
            Label(str(row + 1), font_size=12,
                  x=4, y=row * C.SQUARE_SIZE + C.SQUARE_SIZE // 2,
                  anchor_x="left", anchor_y="center",
                  color=(0, 0, 0, 100)).draw()
            Label(str(row + 1), font_size=12,
                  x=C.BOARD_PX - 4, y=row * C.SQUARE_SIZE + C.SQUARE_SIZE // 2,
                  anchor_x="right", anchor_y="center",
                  color=(0, 0, 0, 100)).draw()

    def _draw_square_border(self, x, y, color):
        b = 3
        shapes.Rectangle(x, y, C.SQUARE_SIZE, b, color=color).draw()
        shapes.Rectangle(x, y + C.SQUARE_SIZE - b, C.SQUARE_SIZE, b, color=color).draw()
        shapes.Rectangle(x, y, b, C.SQUARE_SIZE, color=color).draw()
        shapes.Rectangle(x + C.SQUARE_SIZE - b, y, b, C.SQUARE_SIZE, color=color).draw()

    def draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece is None:
                continue
            if self.selected_square == square:
                if self.dragging:
                    continue
                sprite = pyglet.sprite.Sprite(self.piece_textures[piece.symbol()],
                                              x=chess.square_file(square) * C.SQUARE_SIZE,
                                              y=chess.square_rank(square) * C.SQUARE_SIZE)
                sprite.opacity = 100
                sprite.draw()
            else:
                col = chess.square_file(square)
                row = chess.square_rank(square)
                texture = self.piece_textures[piece.symbol()]
                sprite = pyglet.sprite.Sprite(texture, x=col * C.SQUARE_SIZE, y=row * C.SQUARE_SIZE)
                sprite.draw()

    def draw_dashboard(self):
        rect = shapes.Rectangle(C.BOARD_PX, 0, C.DASHBOARD_WIDTH, C.WINDOW_HEIGHT, color=C.DASHBOARD_BG)
        rect.draw()

        title = Label("Chess AI", font_size=18, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 20,
                      anchor_y="top", color=(255, 255, 255, 255))
        title.draw()

        mode_text = "Mode: PvP" if self.mode == "pvp" else "Mode: PvA"
        mode_label = Label(mode_text, font_size=12, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 50,
                           anchor_y="top", color=(200, 200, 200, 255))
        mode_label.draw()

        time_label = Label(f"Time: {self.game_time//60} ph", font_size=12,
                           x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 75,
                           anchor_y="top", color=(180, 200, 180, 255))
        time_label.draw()

        def fmt(t):
            m = int(t // 60)
            s = int(t % 60)
            return f"{m:02d}:{s:02d}"

        cw, ch = C.DASHBOARD_WIDTH - 20, 28
        cx = C.BOARD_PX + 10

        black_active = self.board.turn == chess.BLACK
        white_active = self.board.turn == chess.WHITE

        for active, label, seconds, y_pos in [
            (black_active, "BLACK", self.time_black, C.WINDOW_HEIGHT - 105),
            (white_active, "WHITE", self.time_white, C.WINDOW_HEIGHT - 137),
        ]:
            bg = (65, 55, 55) if active else (40, 40, 40)
            if seconds <= 0:
                bg = (120, 30, 30)
            shapes.Rectangle(cx, y_pos, cw, ch, color=bg).draw()
            shapes.BorderedRectangle(cx, y_pos, cw, ch, border=1,
                                     color=bg,
                                     border_color=(180, 140, 100, 200)).draw()
            Label(label, font_size=11, x=cx + 6, y=y_pos + ch // 2,
                  anchor_y="center", color=(200, 200, 200, 255)).draw()
            Label(fmt(seconds), font_size=17 if active else 14,
                  x=cx + cw - 6, y=y_pos + ch // 2,
                  anchor_x="right", anchor_y="center",
                  color=(255, 255, 255, 255)).draw()

        moves = Label(f"Moves: {self.move_count}", font_size=12, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 180,
                      anchor_y="top", color=(200, 200, 200, 255))
        moves.draw()

        turn = Label(f"Turn: {'White' if self.board.turn == chess.WHITE else 'Black'}",
                     font_size=12, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 205,
                     anchor_y="top", color=(200, 200, 200, 255))
        turn.draw()

        vol_label = Label(f"Music: {int(self.music_volume * 100)}%",
                          font_size=12, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 230,
                          anchor_y="top", color=(200, 200, 200, 255))
        vol_label.draw()

        book_label = Label(f"Book: {'On' if self.use_opening_book else 'Off'}",
                           font_size=12, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 255,
                           anchor_y="top",
                           color=(100, 200, 100, 255) if self.use_opening_book else (200, 100, 100, 255))
        book_label.draw()

        reset_label = Label("R: Reset  |  ESC: Menu", font_size=11, x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 280,
                            anchor_y="top", color=(150, 150, 150, 255))
        reset_label.draw()

        if self.board.is_game_over() or (not self.clock_running and self.state == "game"):
            reason = ""
            if self.game_result:
                reason = self.game_result
            elif self.time_white <= 0:
                reason = "Black wins (time)"
            elif self.time_black <= 0:
                reason = "White wins (time)"
            elif self.board.is_checkmate():
                reason = f"{'Black' if self.board.turn == chess.WHITE else 'White'} wins"
            elif self.board.is_stalemate():
                reason = "Stalemate"
            elif self.board.is_insufficient_material():
                reason = "Draw (material)"
            elif self.board.can_claim_draw():
                reason = "Draw"
            if reason:
                y = C.WINDOW_HEIGHT - 290
                shapes.Rectangle(C.BOARD_PX + 5, y - 5, C.DASHBOARD_WIDTH - 10, 30,
                                 color=(40, 30, 30)).draw()
                Label(reason, font_size=13, x=C.BOARD_PX + 10, y=y,
                      anchor_y="top", color=(255, 100, 100, 255)).draw()

        self.game_buttons = []
        btn_w, btn_h = C.DASHBOARD_WIDTH - 20, 36
        btn_x = C.BOARD_PX + 10
        btn_data = [
            ("Đầu hàng", (180, 70, 70)),
            ("Cầu hòa", (70, 130, 180)),
        ]
        for i, (text, clr) in enumerate(btn_data):
            by = 90 - i * (btn_h + 8)
            self.game_buttons.append({"rect": (btn_x, by, btn_w, btn_h), "action": text})
            shapes.BorderedRectangle(btn_x, by, btn_w, btn_h, border=2,
                                     color=(*clr, 200),
                                     border_color=(*clr, 200)).draw()
            Label(text, font_size=14,
                  x=btn_x + btn_w // 2, y=by + btn_h // 2,
                  anchor_x="center", anchor_y="center",
                  color=(255, 255, 255, 255)).draw()

        mini_w = (C.DASHBOARD_WIDTH - 28) // 2
        mini_y = 146
        mini_data = [
            ("<", "undo", (90, 90, 100)),
            (">", "redo", (90, 90, 100)),
        ]
        for j, (sym, act, clr) in enumerate(mini_data):
            mx = btn_x + j * (mini_w + 8)
            self.game_buttons.append({"rect": (mx, mini_y, mini_w, btn_h), "action": act})
            shapes.BorderedRectangle(mx, mini_y, mini_w, btn_h, border=2,
                                     color=(*clr, 200),
                                     border_color=(120, 120, 130, 200)).draw()
            Label(sym, font_size=20,
                  x=mx + mini_w // 2, y=mini_y + btn_h // 2,
                  anchor_x="center", anchor_y="center",
                  color=(255, 255, 255, 255)).draw()

        if self.draw_offered_by:
            offer_text = f"{self.draw_offered_by.capitalize()} offered draw"
            Label(offer_text, font_size=11, x=C.BOARD_PX + 10, y=130,
                  anchor_y="top", color=(255, 220, 100, 255)).draw()

    def draw_promotion_dialog(self):
        overlay = shapes.Rectangle(0, 0, C.BOARD_PX, C.BOARD_PX, color=(0, 0, 0, 150))
        overlay.draw()

        pieces = ["Q", "R", "B", "N"]
        labels = ["Hậu", "Xe", "Tượng", "Mã"]
        dialog_y = C.BOARD_PX // 2 - C.SQUARE_SIZE // 2
        dialog_x = C.BOARD_PX // 2 - 2 * C.SQUARE_SIZE

        bg = shapes.Rectangle(dialog_x - 10, dialog_y - 10,
                               4 * C.SQUARE_SIZE + 20, C.SQUARE_SIZE + 60,
                               color=(30, 30, 30, 230))
        bg.draw()

        title = Label("Phong cấp - Chọn quân:", font_size=14,
                      x=C.BOARD_PX // 2, y=dialog_y + C.SQUARE_SIZE + 25,
                      anchor_x="center", anchor_y="center",
                      color=(255, 255, 255, 255))
        title.draw()

        is_white = self.board.turn == chess.WHITE
        for i, sym in enumerate(pieces):
            px = dialog_x + i * C.SQUARE_SIZE
            py = dialog_y
            box = shapes.BorderedRectangle(px, py, C.SQUARE_SIZE, C.SQUARE_SIZE,
                                           color=(60, 60, 60, 200),
                                           border_color=(200, 200, 200, 200),
                                           border=2)
            box.draw()
            key = sym if is_white else sym.lower()
            texture = self.piece_textures[key]
            sprite = pyglet.sprite.Sprite(texture, x=px, y=py)
            sprite.draw()
            name_label = Label(labels[i], font_size=10,
                               x=px + C.SQUARE_SIZE // 2, y=py - 12,
                               anchor_x="center", anchor_y="center",
                               color=(200, 200, 200, 255))
            name_label.draw()

        hint = Label("Click vào quân muốn phong cấp", font_size=11,
                     x=C.BOARD_PX // 2, y=dialog_y - 35,
                     anchor_x="center", anchor_y="center",
                     color=(180, 180, 180, 255))
        hint.draw()

    def draw_editor(self):
        shapes.Rectangle(C.BOARD_PX, 0, C.DASHBOARD_WIDTH, C.WINDOW_HEIGHT, color=C.DASHBOARD_BG).draw()

        cx = C.BOARD_PX + C.DASHBOARD_WIDTH // 2

        title = Label("✏ Board Editor", font_size=16,
                      x=cx, y=C.WINDOW_HEIGHT - 20,
                      anchor_x="center", anchor_y="top",
                      color=(255, 255, 255, 255))
        title.draw()

        fen = self.board.fen()
        fen_label = Label(fen[:50], font_size=9,
                          x=C.BOARD_PX + 10, y=C.WINDOW_HEIGHT - 55,
                          anchor_y="top", color=(180, 180, 180, 255),
                          width=C.DASHBOARD_WIDTH - 20, multiline=True)
        fen_label.draw()

        # Piece palette
        pal_y = C.WINDOW_HEIGHT - 120
        pal_cols = 6
        pal_size = 32
        pal_gap = 3
        pal_start_x = C.BOARD_PX + (C.DASHBOARD_WIDTH - pal_cols * (pal_size + pal_gap)) // 2

        self.editor_buttons = []
        white_symbols = ["K", "Q", "R", "B", "N", "P"]
        black_symbols = ["k", "q", "r", "b", "n", "p"]

        piece_scale = pal_size / 80.0

        for row, symbols in enumerate([white_symbols, black_symbols]):
            for col, sym in enumerate(symbols):
                px = pal_start_x + col * (pal_size + pal_gap)
                py = pal_y - row * (pal_size + pal_gap + 4)
                is_selected = self.editor_palette_piece == sym
                clr = (120, 150, 200, 200) if is_selected else (60, 60, 60, 200)
                bdr = (200, 200, 200, 200) if is_selected else (120, 120, 120, 200)
                shapes.BorderedRectangle(px, py, pal_size, pal_size, border=2,
                                         color=clr,
                                         border_color=bdr).draw()
                spr = pyglet.sprite.Sprite(self.piece_textures[sym],
                                           x=px, y=py)
                spr.scale = piece_scale
                spr.draw()
                self.editor_buttons.append({"rect": (px, py, pal_size, pal_size), "action": "palette", "value": sym})

        # Trash button
        trash_y = pal_y - 2 * (pal_size + pal_gap + 4) - 14
        trash_w = 60
        trash_h = 34
        trash_x = C.BOARD_PX + (C.DASHBOARD_WIDTH - trash_w) // 2
        is_trash = self.editor_palette_piece == "__delete__"
        trash_clr = (200, 70, 70, 220) if is_trash else (70, 60, 60, 200)
        trash_bdr = (255, 120, 120, 220) if is_trash else (120, 120, 120, 200)
        shapes.BorderedRectangle(trash_x, trash_y, trash_w, trash_h, border=2,
                                 color=trash_clr,
                                 border_color=trash_bdr).draw()
        Label("🗑 Xóa", font_size=14,
              x=trash_x + trash_w // 2, y=trash_y + trash_h // 2,
              anchor_x="center", anchor_y="center",
              color=(255, 255, 255, 255)).draw()
        self.editor_buttons.append({"rect": (trash_x, trash_y, trash_w, trash_h), "action": "palette", "value": "__delete__"})

        # Buttons
        btn_w, btn_h = C.DASHBOARD_WIDTH - 20, 34
        btn_x = C.BOARD_PX + 10
        btn_y_start = pal_y - 2 * (pal_size + pal_gap + 4) - 65

        editor_actions = [
            ("Xóa bàn cờ", "clear"),
            ("Vị trí ban đầu", "reset"),
            ("▶ Đánh với người", "play_pvp"),
            ("🤖 Đánh với máy", "play_pva"),
        ]

        for i, (text, action) in enumerate(editor_actions):
            by = btn_y_start - i * (btn_h + 6)
            self.editor_buttons.append({"rect": (btn_x, by, btn_w, btn_h), "action": action, "value": None})
            clr = (70, 100, 70) if action.startswith("play") else (60, 60, 60)
            shapes.BorderedRectangle(btn_x, by, btn_w, btn_h, border=2,
                                     color=(*clr, 200),
                                     border_color=(150, 150, 150, 200)).draw()
            Label(text, font_size=13,
                  x=btn_x + btn_w // 2, y=by + btn_h // 2,
                  anchor_x="center", anchor_y="center",
                  color=(255, 255, 255, 255)).draw()

        instruct = Label("Kéo palette thả vào bàn cờ\nChọn 🗑 rồi click/kéo để xóa",
                         font_size=10, x=cx, y=30,
                         anchor_x="center", anchor_y="center",
                         color=(150, 150, 150, 255))
        instruct.draw()

    def _handle_promotion_click(self, x, y):
        sym = self._promotion_sym_at_pos(x, y)
        if sym is None:
            self._clear_promotion()
            return
        promo_map = {"Q": chess.QUEEN, "R": chess.ROOK, "B": chess.BISHOP, "N": chess.KNIGHT}
        promo = promo_map.get(sym)
        if promo is None:
            return
        for m in self.promotion_moves:
            if m.promotion == promo:
                self.board.push(m)
                self.move_count += 1
                self.last_move_square = self.promotion_to_sq
                self.last_move_from_sq = self.promotion_from_sq
                if self.board.is_check():
                    self._play_sound("check")
                else:
                    self._play_sound("move")
                break
        self._clear_promotion()

        if self.mode == "pva" and not self.board.is_game_over() and not self.ai_thinking:
            self.ai_thinking = True
            pyglet.clock.schedule_once(lambda dt: self._do_ai_move(), 0.1)

    def _promotion_sym_at_pos(self, x, y):
        pieces = ["Q", "R", "B", "N"]
        dialog_y = C.BOARD_PX // 2 - C.SQUARE_SIZE // 2
        dialog_x = C.BOARD_PX // 2 - 2 * C.SQUARE_SIZE
        for i, sym in enumerate(pieces):
            px = dialog_x + i * C.SQUARE_SIZE
            py = dialog_y
            if px <= x <= px + C.SQUARE_SIZE and py <= y <= py + C.SQUARE_SIZE:
                return sym
        return None

    def _handle_game_button(self, action):
        if action == "undo":
            self._undo_move()
            return
        if action == "redo":
            self._redo_move()
            return
        if self.board.is_game_over() or not self.clock_running:
            return
        if action == "Đầu hàng":
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            self.game_result = f"{winner} wins (surrender)"
            self.clock_running = False
            self.draw_offered_by = None
            self._determine_victory_text()
        elif action == "Cầu hòa":
            turn = "white" if self.board.turn == chess.WHITE else "black"
            if self.draw_offered_by is None:
                self.draw_offered_by = turn
            elif self.draw_offered_by == turn:
                self.draw_offered_by = None
            else:
                self.game_result = "Draw (agreement)"
                self.clock_running = False
                self.draw_offered_by = None
                self._determine_victory_text()

    def _handle_editor_drop(self, x, y):
        if x >= C.BOARD_PX:
            return
        square = self.square_from_pos(x, y)
        if square is None:
            return
        sym = self.editor_palette_piece
        if sym == "__delete__":
            self.board.remove_piece_at(square)
            return
        color = chess.WHITE if sym.isupper() else chess.BLACK
        piece_type_map = {
            "K": chess.KING, "Q": chess.QUEEN, "R": chess.ROOK,
            "B": chess.BISHOP, "N": chess.KNIGHT, "P": chess.PAWN,
        }
        pt = piece_type_map.get(sym.upper())
        if pt is not None:
            self.board.set_piece_at(square, chess.Piece(pt, color))

    def square_from_pos(self, x, y):
        col = int(x // C.SQUARE_SIZE)
        row = int(y // C.SQUARE_SIZE)
        if 0 <= col < 8 and 0 <= row < 8:
            return chess.square(col, row)
        return None

    def _handle_editor_click(self, x, y, button):
        # Check dashboard buttons
        if x >= C.BOARD_PX:
            for btn in self.editor_buttons:
                bx, by, bw, bh = btn["rect"]
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    if btn["action"] == "palette":
                        self.editor_palette_piece = btn["value"]
                        self.editor_selected_sq = None
                    elif btn["action"] == "clear":
                        self.board.clear()
                        self.editor_palette_piece = None
                        self.editor_selected_sq = None
                    elif btn["action"] == "reset":
                        self.board.reset()
                        self.editor_palette_piece = None
                        self.editor_selected_sq = None
                    elif btn["action"] in ("play_pvp", "play_pva"):
                        if not self.board.is_valid():
                            print("Bàn cờ không hợp lệ! (Thiếu/dư Vua hoặc sai lượt chiếu)")
                            return
                        self.state = "game"
                        self.mode = "pvp" if btn["action"] == "play_pvp" else "pva"
                        self.selected_square = None
                        self.legal_moves_for_selected.clear()
                        self.move_count = 0
                        self.time_white = float(self.game_time)
                        self.time_black = float(self.game_time)
                        self.clock_running = True
                        self.draw_offered_by = None
                        self.game_result = None
                        self.ai_thinking = False
                        self.last_move_square = None
                        self.last_move_from_sq = None
                        self.victory_text = None
                        self.victory_time = 0.0
                        self.redo_stack.clear()
                        self.editor_palette_piece = None
                        self.editor_selected_sq = None
                        if self.mode == "pva" and self.board.turn == self.ai_color:
                            pyglet.clock.schedule_once(lambda dt: self._do_ai_move(), 0.1)
                    return
            return

        # Click on board
        square = self.square_from_pos(x, y)
        if square is None:
            return

        if button == mouse.RIGHT or self.editor_palette_piece == "__delete__":
            self.board.remove_piece_at(square)
            return

        if self.editor_palette_piece is not None:
            sym = self.editor_palette_piece
            color = chess.WHITE if sym.isupper() else chess.BLACK
            piece_type_map = {
                "K": chess.KING, "Q": chess.QUEEN, "R": chess.ROOK,
                "B": chess.BISHOP, "N": chess.KNIGHT, "P": chess.PAWN,
            }
            pt = piece_type_map.get(sym.upper())
            if pt is not None:
                self.board.set_piece_at(square, chess.Piece(pt, color))
                self.editor_selected_sq = square
