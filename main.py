import tkinter as tk
from tkinter import ttk
import pygame
import chess
from stockfish import Stockfish
from PIL import Image, ImageTk

# Initialize Stockfish
stockfish = Stockfish("AI/stockfish")
class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notation Chess")

        # Configuration variables after initializing root
        self.show_log = tk.BooleanVar(value=True)
        self.show_board = tk.BooleanVar(value=True)
        self.stockfish_difficulty = tk.IntVar(value=5)
        self.play_as_white = tk.BooleanVar(value=True)
        
        # Pygame configuration
        self.board = chess.Board()
        self.move_log = []
        self.highlighted_squares = ([], [])  # (green_squares, red_squares)

        # Position history for arrow-key navigation (view-only)
        self.position_history = [self.board.fen()]  # FEN after each move
        self.view_index = None  # None = live position; 0..len-1 = viewing history
        
        # Piece values for scoring
        self.piece_values = {
            'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0,
            'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0,
        }
        self.piece_symbols = {
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
        }
        # Track initial piece counts to compute captures
        self.initial_counts = self._count_pieces()
        self.tk_piece_images = {}  # loaded after init_pygame (needs pygame)
        self.top_pieces_frame = None
        self.bot_pieces_frame = None
        self.top_points_label = None
        self.bot_points_label = None
        self.black_pieces_frame = None  # compat
        self.white_pieces_frame = None  # compat
        
        self.setup_gui()
        self.init_pygame()
        self._load_tk_piece_images(24)  # small tk-compatible piece images
        self.update_pygame()
        # Current move being typed (keyboard capture)
        self.move_input_text = ""

    def _count_pieces(self, board=None):
        """Returns a dict counting pieces by symbol on the given board (defaults to live)."""
        if board is None:
            board = self.board
        counts = {}
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                symbol = piece.symbol()
                counts[symbol] = counts.get(symbol, 0) + 1
        return counts

    def get_captured_by_white(self, board=None):
        """Returns (list_of_piece_symbols, total_points) captured by White (black pieces off board)."""
        current = self._count_pieces(board)
        captured = []
        total = 0
        for symbol in ['p', 'n', 'b', 'r', 'q']:  # black pieces (lowercase)
            initial = self.initial_counts.get(symbol, 0)
            now = current.get(symbol, 0)
            missing = initial - now
            if missing > 0:
                captured.extend([symbol] * missing)
                total += self.piece_values[symbol] * missing
        return captured, total

    def get_captured_by_black(self, board=None):
        """Returns (list_of_piece_symbols, total_points) captured by Black (white pieces off board)."""
        current = self._count_pieces(board)
        captured = []
        total = 0
        for symbol in ['P', 'N', 'B', 'R', 'Q']:  # white pieces (uppercase)
            initial = self.initial_counts.get(symbol, 0)
            now = current.get(symbol, 0)
            missing = initial - now
            if missing > 0:
                captured.extend([symbol] * missing)
                total += self.piece_values[symbol] * missing
        return captured, total

    def _load_tk_piece_images(self, size):
        """Loads small PIL ImageTk images of pieces for the captured panel."""
        pieces = {
            'r': 'rb.png', 'n': 'nb.png', 'b': 'bb.png', 'q': 'qb.png', 'k': 'kb.png', 'p': 'pb.png',
            'R': 'rw.png', 'N': 'nw.png', 'B': 'bw.png', 'Q': 'qw.png', 'K': 'kw.png', 'P': 'pw.png'
        }
        for symbol, filename in pieces.items():
            img = Image.open(f'images/{filename}')
            img = img.resize((size, size), Image.LANCZOS)
            self.tk_piece_images[symbol] = ImageTk.PhotoImage(img)

    def update_captured_display(self, board=None):
        """Updates the captured pieces panel with small piece images.
        Top row = pieces the opponent captured (what you lost).
        Bottom row = pieces you captured (opponent's pieces you took).
        If board is given, computes captures for that board (used in review mode)."""
        if self.top_pieces_frame is None or self.bot_pieces_frame is None:
            return
        black_captured, black_total = self.get_captured_by_white(board)
        white_captured, white_total = self.get_captured_by_black(board)

        play_white = self.play_as_white.get()

        # Determine which captured set goes on top (enemy's captures / what you lost)
        if play_white:
            top_captured, top_total = white_captured, white_total   # white pieces black took
            bot_captured, bot_total = black_captured, black_total   # black pieces white took
            top_frame, top_label = self.top_pieces_frame, self.top_points_label
            bot_frame, bot_label = self.bot_pieces_frame, self.bot_points_label
        else:
            top_captured, top_total = black_captured, black_total   # black pieces white took
            bot_captured, bot_total = white_captured, white_total   # white pieces black took
            top_frame, top_label = self.top_pieces_frame, self.top_points_label
            bot_frame, bot_label = self.bot_pieces_frame, self.bot_points_label

        # Rebuild top row (pieces you lost)
        for w in top_frame.winfo_children():
            w.destroy()
        for symbol in top_captured:
            if symbol in self.tk_piece_images:
                lbl = tk.Label(top_frame, image=self.tk_piece_images[symbol])
                lbl.pack(side=tk.LEFT)
        top_label.config(text=f"+{top_total}" if top_total > 0 else "")

        # Rebuild bottom row (pieces you captured)
        for w in bot_frame.winfo_children():
            w.destroy()
        for symbol in bot_captured:
            if symbol in self.tk_piece_images:
                lbl = tk.Label(bot_frame, image=self.tk_piece_images[symbol])
                lbl.pack(side=tk.LEFT)
        bot_label.config(text=f"+{bot_total}" if bot_total > 0 else "")

    def setup_gui(self):
        # Top menu
        menu_bar = tk.Menu(self.root)
        game_menu = tk.Menu(menu_bar, tearoff=0)
        game_menu.add_command(label="New Game", command=self.new_game)
        game_menu.add_separator()
        game_menu.add_checkbutton(label="Play as White", variable=self.play_as_white, command=self.toggle_player_color)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="Game", menu=game_menu)

        options_menu = tk.Menu(menu_bar, tearoff=0)
        options_menu.add_checkbutton(label="Show Move Log", variable=self.show_log)
        options_menu.add_checkbutton(label="Show Board", variable=self.show_board, command=self.toggle_board_visibility)
        options_menu.add_separator()
        options_menu.add_command(label="Copy Log to Clipboard", command=self.copy_log_to_clipboard)
        menu_bar.add_cascade(label="Options", menu=options_menu)
        self.root.config(menu=menu_bar)
        
        # Settings section
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # Label displaying Stockfish level
        self.stockfish_level_label = tk.Label(settings_frame, text=f"Stockfish: Level {self.stockfish_difficulty.get()}")
        self.stockfish_level_label.pack(anchor=tk.W)
        
        # Slider to adjust Stockfish level with callback to update Label
        difficulty_slider = ttk.Scale(
            settings_frame, from_=1, to=20, variable=self.stockfish_difficulty,
            orient=tk.HORIZONTAL, command=self.update_stockfish_level_label
        )
        difficulty_slider.pack(anchor=tk.W)
        
        # Move log with columns
        tk.Label(settings_frame, text="Move Log:").pack(anchor=tk.W, pady=(10,0))
        
        # Frame for treeview and scrollbar
        log_frame = tk.Frame(settings_frame)
        log_frame.pack(anchor=tk.W, pady=5)
        
        # Treeview with 3 columns
        self.log_tree = ttk.Treeview(log_frame, columns=("white", "black"), show="tree headings", height=12)
        self.log_tree.heading("#0", text="#")
        self.log_tree.heading("white", text="White")
        self.log_tree.heading("black", text="Black")
        
        # Configure column widths
        self.log_tree.column("#0", width=50, minwidth=50)
        self.log_tree.column("white", width=80, minwidth=80)
        self.log_tree.column("black", width=80, minwidth=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        
        self.log_tree.pack(side="left")
        scrollbar.pack(side="right", fill="y")

        # --- Captured Pieces / Score Panel ---
        captured_frame = tk.LabelFrame(settings_frame, text="Captured Pieces", padx=5, pady=5)
        captured_frame.pack(anchor=tk.W, pady=(10, 0), fill=tk.X)

        # Top row: pieces the opponent captured (what you lost)
        top_row = tk.Frame(captured_frame)
        top_row.pack(anchor=tk.W, fill=tk.X)
        self.top_pieces_frame = tk.Frame(top_row)
        self.top_pieces_frame.pack(side=tk.LEFT)
        self.top_points_label = tk.Label(top_row, text="", font=("TkDefaultFont", 10, "bold"), fg="#cc3333")
        self.top_points_label.pack(side=tk.LEFT, padx=(4, 0))
        # compat aliases (will be overwritten by update_captured_display logic)
        self.white_pieces_frame = self.top_pieces_frame
        self.white_points_label = self.top_points_label

        # Bottom row: pieces you captured (opponent's pieces you took)
        bot_row = tk.Frame(captured_frame)
        bot_row.pack(anchor=tk.W, fill=tk.X)
        self.bot_pieces_frame = tk.Frame(bot_row)
        self.bot_pieces_frame.pack(side=tk.LEFT)
        self.bot_points_label = tk.Label(bot_row, text="", font=("TkDefaultFont", 10, "bold"), fg="#33aa33")
        self.bot_points_label.pack(side=tk.LEFT, padx=(4, 0))
        # compat aliases
        self.black_pieces_frame = self.bot_pieces_frame
        self.black_points_label = self.bot_points_label

        # Move display — large title-style component
        self.move_display_label = tk.Label(settings_frame, text="",
            font=("Courier", 32, "bold"),
            anchor=tk.W, relief=tk.SUNKEN, padx=12, pady=8,
            bg="#fffff0", fg="#333333")
        self.move_display_label.pack(anchor=tk.W, pady=(2, 0), fill=tk.X)

        # Bind keyboard for move input (global capture)
        self.root.bind("<KeyPress>", self.on_key_press)
        
        # Bind arrow keys for move history navigation (view-only)
        self.root.bind("<Left>", self.navigate_back)
        self.root.bind("<Right>", self.navigate_forward)
        self.root.bind("<Up>", self.navigate_first)
        self.root.bind("<Down>", self.navigate_last)
        
        # Pygame display settings on Tkinter Canvas
        self.canvas = tk.Canvas(self.root, width=720, height=720)
        self.canvas.pack(side=tk.RIGHT, padx=10, pady=10)

    def update_stockfish_level_label(self, event=None):
        """Updates the Stockfish level label as the slider moves."""
        self.stockfish_level_label.config(text=f"Stockfish: Level {self.stockfish_difficulty.get()}")
    
    def toggle_board_visibility(self):
        """Toggles between showing/hiding the board (blind chess mode)."""
        if self.show_board.get():
            # Show board
            self.canvas.pack(side=tk.RIGHT, padx=10, pady=10)
        else:
            # Hide board (blind chess mode)
            self.canvas.pack_forget()

    def navigate_back(self, event=None):
        """Left arrow: go back one move in history (view-only)."""
        if len(self.position_history) <= 1:
            return  # No moves to navigate back to
        if self.view_index is None:
            # Currently live — start viewing from the last position
            self.view_index = len(self.position_history) - 2  # one before last
        else:
            self.view_index = max(0, self.view_index - 1)
        self._update_review_mode_ui()

    def navigate_forward(self, event=None):
        """Right arrow: go forward one move in history (view-only)."""
        if self.view_index is not None:
            if self.view_index < len(self.position_history) - 2:
                self.view_index += 1
            else:
                # Reached the end — go back to live
                self.view_index = None
        self._update_review_mode_ui()

    def navigate_first(self, event=None):
        """Up arrow: go to the first position in history."""
        if len(self.position_history) > 1:
            self.view_index = 0
        self._update_review_mode_ui()

    def navigate_last(self, event=None):
        """Down arrow: go back to live (latest) position."""
        self.view_index = None
        self._update_review_mode_ui()

    def _update_review_mode_ui(self):
        """Updates UI elements to reflect review mode state."""
        if self.view_index is not None:
            self.move_display_label.config(text="", fg="#333333")
            # Show captured pieces for the historical position
            hist_board = chess.Board()
            hist_board.set_fen(self.position_history[self.view_index])
            self.update_captured_display(hist_board)
        else:
            self.move_display_label.config(text=self.move_input_text, fg="#333333")
            # Restore live captured pieces
            self.update_captured_display()

    def on_key_press(self, event):
        """Global keyboard handler for move input."""
        # Don't process input in review mode
        if self.view_index is not None:
            return

        keysym = event.keysym

        # Let arrow keys pass through (handled by separate bindings)
        if keysym in ('Left', 'Right', 'Up', 'Down'):
            return

        # Submit move
        if keysym in ('Return', 'space'):
            self.submit_move()
            return 'break'

        # Clear input
        if keysym in ('BackSpace', 'Escape'):
            self.move_input_text = ""
            self.update_move_display()
            self.highlighted_squares = ([], [])
            return 'break'

        char = event.char
        if not char or not char.isprintable():
            return 'break'

        # Allowed characters for algebraic notation
        allowed = set('abcdefgh12345678xX+-=#rbqnkRBQNKOo')
        if char not in allowed:
            return 'break'

        # Build candidate and normalize
        candidate = self.move_input_text + char
        candidate = self._normalize_notation(candidate)

        # Only accept if it's a valid prefix of some legal move
        if self._is_valid_prefix(candidate):
            self.move_input_text = candidate
            self.update_move_display()
            self._update_highlights()

        return 'break'

    def _normalize_notation(self, text):
        """Normalizes move input: capitalizes piece letters and castling 'O'.
        Also inserts hyphens for O-O / O-O-O notation.
        'b' is special: tries lowercase (pawn b-file) first, falls back to 'B' (bishop)."""
        if not text:
            return text
        # Capitalize piece identifiers (R, N, Q, K) and castling O at start
        result = text
        if result[0].lower() in 'rqnko':
            result = result[0].upper() + result[1:]
        # Handle 'b' ambiguity: try pawn b-file first, fall back to bishop
        if result and result[0] == 'b':
            if not self._is_valid_prefix(result):
                alt = 'B' + result[1:]
                if self._is_valid_prefix(alt):
                    result = alt
        # In castling notation, turn all 'o' into 'O' (O-O, O-O-O)
        if result and result[0] == 'O':
            result = result[0] + result[1:].replace('o', 'O')
            # Auto-insert hyphens: OOO -> O-O-O, OO -> O-O (if no hyphen typed yet)
            if '-' not in result:
                if result == 'OOO':
                    result = 'O-O-O'
                elif result == 'OO':
                    result = 'O-O'
        return result

    def _is_valid_prefix(self, prefix):
        """Returns True if any legal SAN move starts with the given prefix."""
        for move in self.board.legal_moves:
            try:
                if self.board.san(move).startswith(prefix):
                    return True
            except Exception:
                pass
        return False

    def _update_highlights(self):
        """Highlights squares based on current move_input_text."""
        text = self.move_input_text
        if not text:
            self.highlighted_squares = ([], [])
            return
        green_squares = []
        red_squares = []
        for move in self.board.legal_moves:
            try:
                if self.board.san(move).startswith(text):
                    green_squares.append(move.from_square)
                    red_squares.append(move.to_square)
            except Exception:
                pass
        self.highlighted_squares = (green_squares, red_squares)

    def update_move_display(self):
        """Updates the move display label with current input."""
        if self.view_index is not None:
            return
        self.move_display_label.config(text=self.move_input_text, fg="#333333")

    def get_display_board(self):
        """Returns the board to display (historical if in review mode, else live)."""
        if self.view_index is not None and 0 <= self.view_index < len(self.position_history):
            b = chess.Board()
            b.set_fen(self.position_history[self.view_index])
            return b
        return self.board

    def init_pygame(self):
        pygame.init()
        self.screen = pygame.Surface((720, 720))
        self.colors = [pygame.Color("white"), pygame.Color("gray")]
        self.font = pygame.font.Font(None, 36)
        self.images = self.load_images(80)

    def load_images(self, square_size):
        pieces = {
            'r': 'rb.png', 'n': 'nb.png', 'b': 'bb.png', 'q': 'qb.png', 'k': 'kb.png', 'p': 'pb.png',
            'R': 'rw.png', 'N': 'nw.png', 'B': 'bw.png', 'Q': 'qw.png', 'K': 'kw.png', 'P': 'pw.png'
        }
        images = {}
        for piece, filename in pieces.items():
            image = pygame.image.load(f'images/{filename}')
            images[piece] = pygame.transform.smoothscale(image, (square_size, square_size))
        return images

    def update_pygame(self):
        # Only update if the board is visible
        if not self.show_board.get():
            self.root.after(50, self.update_pygame)
            return
            
        self.screen.fill(pygame.Color("black"))
        square_size = 80
        board_offset = 40  # Space for coordinates

        display_board = self.get_display_board()
        
        # Draw the board
        for r in range(8):
            for c in range(8):
                color = self.colors[(r + c) % 2]
                pygame.draw.rect(self.screen, color, 
                               pygame.Rect(c * square_size + board_offset, 
                                         r * square_size + board_offset, 
                                         square_size, square_size))
                
                piece = display_board.piece_at(chess.square(c, 7 - r))
                
                if piece:
                    piece_img = self.images[piece.symbol()]
                    self.screen.blit(piece_img, (c * square_size + board_offset, 
                                               r * square_size + board_offset))
        
        # Draw highlights from move entry input (only when not in review mode)
        if self.view_index is None:
            green_squares, red_squares = self.highlighted_squares
        else:
            green_squares, red_squares = [], []
            
        green_overlay = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
        green_overlay.fill((0, 200, 0, 90))  # light transparent green
        red_overlay = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
        red_overlay.fill((220, 50, 50, 100))  # light transparent red
        
        for sq in green_squares:
            file_idx = chess.square_file(sq)
            rank_idx = 7 - chess.square_rank(sq)
            self.screen.blit(green_overlay, (file_idx * square_size + board_offset,
                                            rank_idx * square_size + board_offset))
        
        for sq in red_squares:
            file_idx = chess.square_file(sq)
            rank_idx = 7 - chess.square_rank(sq)
            self.screen.blit(red_overlay, (file_idx * square_size + board_offset,
                                           rank_idx * square_size + board_offset))
        
        # Draw coordinates
        coord_font = pygame.font.Font(None, 24)
        
        # Letters A-H (columns)
        for c in range(8):
            letter = chr(ord('A') + c)
            text = coord_font.render(letter, True, pygame.Color("white"))
            text_rect = text.get_rect(center=(c * square_size + board_offset + square_size // 2, 20))
            self.screen.blit(text, text_rect)
            # Repeat at bottom
            text_rect = text.get_rect(center=(c * square_size + board_offset + square_size // 2, 
                                            8 * square_size + board_offset + 20))
            self.screen.blit(text, text_rect)
        
        # Numbers 1-8 (rows)
        for r in range(8):
            number = str(8 - r)  # Invert because board is flipped
            text = coord_font.render(number, True, pygame.Color("white"))
            text_rect = text.get_rect(center=(20, r * square_size + board_offset + square_size // 2))
            self.screen.blit(text, text_rect)
            # Repeat on the right
            text_rect = text.get_rect(center=(8 * square_size + board_offset + 20, 
                                            r * square_size + board_offset + square_size // 2))
            self.screen.blit(text, text_rect)

        pil_image = Image.frombytes("RGB", self.screen.get_size(), pygame.image.tostring(self.screen, "RGB"))
        self.tk_image = ImageTk.PhotoImage(pil_image)
        
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.root.after(50, self.update_pygame)
    
    def new_game(self):
        self.board.reset()
        self.move_log.clear()
        # Clear the treeview
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        # Clear highlights
        self.highlighted_squares = ([], [])
        
        # Clear move input
        self.move_input_text = ""
        self.update_move_display()
        
        # Reset position history and review mode
        self.position_history = [self.board.fen()]
        self.view_index = None
        self._update_review_mode_ui()
        
        # Reset piece tracking
        self.initial_counts = self._count_pieces()
        self.update_captured_display()
        
        # If playing as black, make AI play first
        if not self.play_as_white.get():
            self.ai_move()

    def submit_move(self, event=None):
        # Reject moves while in review mode
        if self.view_index is not None:
            print("Cannot move in review mode. Press Down arrow to return to live game.")
            return

        move_text = self.move_input_text
        if not move_text:
            return
        move = self.parse_algebraic(move_text)

        if move and move in self.board.legal_moves:
            # Check if it's the player's turn
            player_is_white = self.play_as_white.get()
            is_white_turn = self.board.turn == chess.WHITE
            
            if (player_is_white and is_white_turn) or (not player_is_white and not is_white_turn):
                self.add_to_log(move)  # Log BEFORE executing the move
                self.board.push(move)
                self.position_history.append(self.board.fen())
                self.update_captured_display()
                self.move_input_text = ""
                self.update_move_display()
                self.highlighted_squares = ([], [])  # Clear highlights
                self.ai_move()  # Call AI to make its move
            else:
                print("Not your turn!")
        else:
            print("Invalid move, try again.")

    def add_to_log(self, move):
        if self.show_log.get():
            try:
                # Convert to SAN (Standard Algebraic Notation) - e.g. e4, Nf3, O-O
                move_san = self.board.san(move)
                self.move_log.append(move_san)
                
                move_number = (len(self.move_log) + 1) // 2
                
                if len(self.move_log) % 2 == 1:  # White's move
                    # Create new row for the move
                    item_id = self.log_tree.insert("", "end", text=str(move_number), values=[move_san, ""])
                else:  # Black's move
                    # Update existing row with Black's move
                    items = self.log_tree.get_children()
                    if items:
                        last_item = items[-1]
                        current_values = self.log_tree.item(last_item)['values']
                        self.log_tree.item(last_item, values=[current_values[0], move_san])
                
                # Auto-scroll to the last move
                items = self.log_tree.get_children()
                if items:
                    self.log_tree.see(items[-1])
                
                print(f"Added to log: {move_san}")
            except Exception as e:
                print(f"Error adding to log: {e}")

    def parse_algebraic(self, notation):
        """Converts algebraic notation to a `chess.Move` object, if valid."""
        try:
            move = self.board.parse_san(notation)
            return move
        except ValueError:
            return None

    def ai_move(self):
        """Executes the AI move."""
        if self.board.is_game_over():
            return
        
        # Get difficulty level from the slider
        skill_level = self.stockfish_difficulty.get()
        print("skill_level: " + str(skill_level))
        stockfish.set_skill_level(skill_level)  # Set difficulty from slider value
        
        stockfish.set_fen_position(self.board.fen()) # Update Stockfish
        
        ai_move = stockfish.get_best_move()
        if ai_move:
            move = chess.Move.from_uci(ai_move)
            if move in self.board.legal_moves:
                self.add_to_log(move)  # Log BEFORE executing the move
                self.board.push(move)
                self.position_history.append(self.board.fen())
                self.update_captured_display()
    
    def toggle_player_color(self):
        """Toggles between playing as white or black."""
        self.new_game()  # Restart the game with the new color
    
    def copy_log_to_clipboard(self):
        """Copies the move log to the clipboard in PGN format."""
        try:
            pgn_moves = []
            for i in range(0, len(self.move_log), 2):
                move_number = (i // 2) + 1
                white_move = self.move_log[i]
                black_move = self.move_log[i + 1] if i + 1 < len(self.move_log) else ""
                
                if black_move:
                    pgn_moves.append(f"{move_number}. {white_move} {black_move}")
                else:
                    pgn_moves.append(f"{move_number}. {white_move}")
            
            pgn_text = " ".join(pgn_moves)
            self.root.clipboard_clear()
            self.root.clipboard_append(pgn_text)
            print("Log copied to clipboard:", pgn_text)
        except Exception as e:
            print(f"Error copying log: {e}")

# Initialize the tkinter app
root = tk.Tk()
app = ChessApp(root)
root.mainloop()
