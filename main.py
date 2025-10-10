import tkinter as tk
from tkinter import ttk
import pygame
import chess
from stockfish import Stockfish
from PIL import Image, ImageTk

# Inicializa o Stockfish
stockfish = Stockfish("AI/stockfish-ubuntu-x86-64-avx2")
class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notation Chess")

        # Variáveis de configuração após inicializar root
        self.show_log = tk.BooleanVar(value=True)
        self.show_board = tk.BooleanVar(value=True)
        self.stockfish_difficulty = tk.IntVar(value=5)
        
        # Configuração do Pygame
        self.board = chess.Board()
        self.move_log = []
        
        self.setup_gui()
        self.init_pygame()
        self.update_pygame()

    def setup_gui(self):
        # Menu superior
        menu_bar = tk.Menu(self.root)
        game_menu = tk.Menu(menu_bar, tearoff=0)
        game_menu.add_command(label="Novo Jogo", command=self.new_game)
        game_menu.add_separator()
        game_menu.add_command(label="Sair", command=self.root.quit)
        menu_bar.add_cascade(label="Jogo", menu=game_menu)

        options_menu = tk.Menu(menu_bar, tearoff=0)
        options_menu.add_checkbutton(label="Mostrar Log de Movimentos", variable=self.show_log)
        options_menu.add_checkbutton(label="Mostrar Tabuleiro", variable=self.show_board)
        menu_bar.add_cascade(label="Opções", menu=options_menu)
        self.root.config(menu=menu_bar)
        
        # Seção de configurações
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # Label que exibe o nível do Stockfish
        self.stockfish_level_label = tk.Label(settings_frame, text=f"Stockfish: lvl {self.stockfish_difficulty.get()}")
        self.stockfish_level_label.pack(anchor=tk.W)
        
        # Slider para ajustar o nível do Stockfish com callback para atualizar o Label
        difficulty_slider = ttk.Scale(
            settings_frame, from_=1, to=20, variable=self.stockfish_difficulty,
            orient=tk.HORIZONTAL, command=self.update_stockfish_level_label
        )
        difficulty_slider.pack(anchor=tk.W)
        
        self.log_text = tk.Text(settings_frame, width=20, height=15)
        self.log_text.pack(anchor=tk.W)

        # Campo de entrada de texto para movimentos ou comandos
        tk.Label(settings_frame, text="Digite seu movimento:").pack(anchor=tk.W)
        self.move_entry = tk.Entry(settings_frame)
        self.move_entry.pack(anchor=tk.W, pady=5)

        # Bind para a tecla Enter
        self.move_entry.bind("<Return>", self.submit_move)
        
        # Configurações de exibição Pygame no Canvas do Tkinter
        self.canvas = tk.Canvas(self.root, width=720, height=720)
        self.canvas.pack(side=tk.RIGHT, padx=10, pady=10)

    def update_stockfish_level_label(self, event=None):
        """Atualiza o Label do nível do Stockfish conforme o slider é movido."""
        self.stockfish_level_label.config(text=f"Stockfish: lvl {self.stockfish_difficulty.get()}")

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
        if not self.show_board.get():
            # Modo blind chess - esconde o tabuleiro
            self.screen.fill(pygame.Color("black"))
            # Texto indicando modo blind chess
            text = self.font.render("Modo Blind Chess", True, pygame.Color("white"))
            text_rect = text.get_rect(center=(360, 360))
            self.screen.blit(text, text_rect)
        else:
            self.screen.fill(pygame.Color("black"))
            square_size = 80
            board_offset = 40  # Espaço para coordenadas
            
            # Desenha o tabuleiro
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
            
            # Desenha as coordenadas
            coord_font = pygame.font.Font(None, 24)
            
            # Letras A-H (coluna)
            for c in range(8):
                letter = chr(ord('A') + c)
                text = coord_font.render(letter, True, pygame.Color("white"))
                text_rect = text.get_rect(center=(c * square_size + board_offset + square_size // 2, 20))
                self.screen.blit(text, text_rect)
                # Repetir embaixo
                text_rect = text.get_rect(center=(c * square_size + board_offset + square_size // 2, 
                                                8 * square_size + board_offset + 20))
                self.screen.blit(text, text_rect)
            
            # Números 1-8 (linha)
            for r in range(8):
                number = str(8 - r)  # Inverter porque o tabuleiro está invertido
                text = coord_font.render(number, True, pygame.Color("white"))
                text_rect = text.get_rect(center=(20, r * square_size + board_offset + square_size // 2))
                self.screen.blit(text, text_rect)
                # Repetir à direita
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
        self.log_text.delete(1.0, tk.END)

    def submit_move(self, event=None):
        # Lê o movimento do campo de entrada e aplica ao tabuleiro
        move_text = self.move_entry.get()
        move = self.parse_algebraic(move_text)

        if move and move in self.board.legal_moves:
            self.add_to_log(move)  # Log ANTES de executar o movimento
            self.board.push(move)
            self.move_entry.delete(0, tk.END)
            self.ai_move()  # Chama a IA para fazer o movimento
        else:
            # Adicione um feedback visual ou textual para o usuário quando o movimento for inválido
            print("Movimento inválido, tente novamente.")

    def add_to_log(self, move):
        if self.show_log.get():
            try:
                # Converte para notação SAN (algebraic notation) - ex: e4, Nf3, O-O
                move_san = self.board.san(move)
                self.move_log.append(move_san)
                
                # Numera os movimentos (1. e4 e5 2. Nf3 Nc6...)
                move_number = (len(self.move_log) + 1) // 2
                if len(self.move_log) % 2 == 1:  # Movimento das brancas
                    move_text = f"{move_number}. {move_san}"
                else:  # Movimento das pretas
                    move_text = f" {move_san}\n"
                
                self.log_text.configure(state="normal")
                self.log_text.insert(tk.END, move_text)
                self.log_text.see(tk.END)
                self.log_text.configure(state="disabled")
                self.root.update()
                print(f"Adicionado ao log: {move_san}")
            except Exception as e:
                print(f"Erro ao adicionar no log: {e}")

    def parse_algebraic(self, notation):
        """Converte notação algébrica em um objeto `chess.Move`, caso válido."""
        try:
            move = self.board.parse_san(notation)
            return move
        except ValueError:
            return None

    def ai_move(self):
        """Executa o movimento da IA."""
        if self.board.is_game_over():
            return
        
        # Obtém o nível de dificuldade do slider
        skill_level = self.stockfish_difficulty.get()
        print("skill_level: " + str(skill_level))
        stockfish.set_skill_level(skill_level)  # Define a dificuldade com o valor do slider
        
        stockfish.set_fen_position(self.board.fen()) # Atualiza o Stockfish
        
        ai_move = stockfish.get_best_move()
        if ai_move:
            move = chess.Move.from_uci(ai_move)
            if move in self.board.legal_moves:
                self.add_to_log(move)  # Log ANTES de executar o movimento
                self.board.push(move)

# Inicializa o aplicativo tkinter
root = tk.Tk()
app = ChessApp(root)
root.mainloop()
