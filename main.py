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
        
        self.setup_gui()
        self.init_pygame()
        self.update_pygame()

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

        # Move input field
        tk.Label(settings_frame, text="Enter your move:").pack(anchor=tk.W)
        self.move_var = tk.StringVar()
        self.move_var.trace_add("write", self.on_move_entry_change)
        self.move_entry = tk.Entry(settings_frame, textvariable=self.move_var)
        self.move_entry.pack(anchor=tk.W, pady=5)

        # Bind Enter key
        self.move_entry.bind("<Return>", self.submit_move)
        
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
        
        # Draw the board
        for r in range(8):
            for c in range(8):
                color = self.colors[(r + c) % 2]
                pygame.draw.rect(self.screen, color, 
                               pygame.Rect(c * square_size + board_offset, 
                                         r * square_size + board_offset, 
                                         square_size, square_size))
                
                piece = self.board.piece_at(chess.square(c, 7 - r))
                
                if piece:
                    piece_img = self.images[piece.symbol()]
                    self.screen.blit(piece_img, (c * square_size + board_offset, 
                                               r * square_size + board_offset))
        
        # Draw highlights from move entry input
        green_squares, red_squares = self.highlighted_squares
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
        
        # If playing as black, make AI play first
        if not self.play_as_white.get():
            self.ai_move()

    def submit_move(self, event=None):
        # Read move from input field and apply to board
        move_text = self.move_entry.get()
        move = self.parse_algebraic(move_text)

        if move and move in self.board.legal_moves:
            # Check if it's the player's turn
            player_is_white = self.play_as_white.get()
            is_white_turn = self.board.turn == chess.WHITE
            
            if (player_is_white and is_white_turn) or (not player_is_white and not is_white_turn):
                self.add_to_log(move)  # Log BEFORE executing the move
                self.board.push(move)
                self.move_entry.delete(0, tk.END)
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

    def on_move_entry_change(self, *args):
        """Highlights squares based on partial SAN input as the user types.
        Green: piece's current square. Red: possible destination squares."""
        text = self.move_var.get().strip()
        if not text:
            self.highlighted_squares = ([], [])
            return
        
        green_squares = []
        red_squares = []
        
        for move in self.board.legal_moves:
            try:
                san = self.board.san(move)
                if san.startswith(text):
                    green_squares.append(move.from_square)
                    red_squares.append(move.to_square)
            except Exception:
                pass
        
        self.highlighted_squares = (green_squares, red_squares)

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
