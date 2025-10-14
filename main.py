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
        self.play_as_white = tk.BooleanVar(value=True)
        
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
        game_menu.add_checkbutton(label="Jogar com Brancas", variable=self.play_as_white, command=self.toggle_player_color)
        game_menu.add_separator()
        game_menu.add_command(label="Sair", command=self.root.quit)
        menu_bar.add_cascade(label="Jogo", menu=game_menu)

        options_menu = tk.Menu(menu_bar, tearoff=0)
        options_menu.add_checkbutton(label="Mostrar Log de Movimentos", variable=self.show_log)
        options_menu.add_checkbutton(label="Mostrar Tabuleiro", variable=self.show_board, command=self.toggle_board_visibility)
        options_menu.add_separator()
        options_menu.add_command(label="Copiar Log para Clipboard", command=self.copy_log_to_clipboard)
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
        
        # Log de movimentos com colunas
        tk.Label(settings_frame, text="Log de Movimentos:").pack(anchor=tk.W, pady=(10,0))
        
        # Frame para o treeview e scrollbar
        log_frame = tk.Frame(settings_frame)
        log_frame.pack(anchor=tk.W, pady=5)
        
        # Treeview com 3 colunas
        self.log_tree = ttk.Treeview(log_frame, columns=("brancas", "pretas"), show="tree headings", height=12)
        self.log_tree.heading("#0", text="Jogada")
        self.log_tree.heading("brancas", text="Brancas")
        self.log_tree.heading("pretas", text="Pretas")
        
        # Configurar largura das colunas
        self.log_tree.column("#0", width=50, minwidth=50)
        self.log_tree.column("brancas", width=80, minwidth=80)
        self.log_tree.column("pretas", width=80, minwidth=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        
        self.log_tree.pack(side="left")
        scrollbar.pack(side="right", fill="y")

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
    
    def toggle_board_visibility(self):
        """Alterna entre mostrar/esconder o tabuleiro (modo blind chess)."""
        if self.show_board.get():
            # Mostrar tabuleiro
            self.canvas.pack(side=tk.RIGHT, padx=10, pady=10)
        else:
            # Esconder tabuleiro (modo blind chess)
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
        # Só atualiza se o tabuleiro estiver visível
        if not self.show_board.get():
            self.root.after(50, self.update_pygame)
            return
            
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
        # Limpar o treeview
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        # Se jogando com pretas, fazer a IA jogar primeiro
        if not self.play_as_white.get():
            self.ai_move()

    def submit_move(self, event=None):
        # Lê o movimento do campo de entrada e aplica ao tabuleiro
        move_text = self.move_entry.get()
        move = self.parse_algebraic(move_text)

        if move and move in self.board.legal_moves:
            # Verificar se é a vez do jogador
            player_is_white = self.play_as_white.get()
            is_white_turn = self.board.turn == chess.WHITE
            
            if (player_is_white and is_white_turn) or (not player_is_white and not is_white_turn):
                self.add_to_log(move)  # Log ANTES de executar o movimento
                self.board.push(move)
                self.move_entry.delete(0, tk.END)
                self.ai_move()  # Chama a IA para fazer o movimento
            else:
                print("Não é sua vez!")
        else:
            # Adicione um feedback visual ou textual para o usuário quando o movimento for inválido
            print("Movimento inválido, tente novamente.")

    def add_to_log(self, move):
        if self.show_log.get():
            try:
                # Converte para notação SAN (algebraic notation) - ex: e4, Nf3, O-O
                move_san = self.board.san(move)
                self.move_log.append(move_san)
                
                move_number = (len(self.move_log) + 1) // 2
                
                if len(self.move_log) % 2 == 1:  # Movimento das brancas
                    # Criar nova linha para a jogada
                    item_id = self.log_tree.insert("", "end", text=str(move_number), values=[move_san, ""])
                else:  # Movimento das pretas
                    # Atualizar a linha existente com o movimento das pretas
                    items = self.log_tree.get_children()
                    if items:
                        last_item = items[-1]
                        current_values = self.log_tree.item(last_item)['values']
                        self.log_tree.item(last_item, values=[current_values[0], move_san])
                
                # Auto-scroll para a última jogada
                items = self.log_tree.get_children()
                if items:
                    self.log_tree.see(items[-1])
                
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
    
    def toggle_player_color(self):
        """Alterna entre jogar com brancas ou pretas."""
        self.new_game()  # Reinicia o jogo com a nova cor
    
    def copy_log_to_clipboard(self):
        """Copia o log de movimentos para o clipboard em formato PGN."""
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
            print("Log copiado para o clipboard:", pgn_text)
        except Exception as e:
            print(f"Erro ao copiar log: {e}")

# Inicializa o aplicativo tkinter
root = tk.Tk()
app = ChessApp(root)
root.mainloop()
