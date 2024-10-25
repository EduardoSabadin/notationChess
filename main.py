import pygame
import chess
from stockfish import Stockfish

# Inicializa pygame
pygame.init()

# Define as cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
RED = (255, 0, 0)

# Inicializa o Stockfish
stockfish = Stockfish("AI/stockfish-ubuntu-x86-64-avx2")  # Substitua pelo caminho para o executável
stockfish.set_skill_level(5)  # Define o nível de dificuldade

# Carrega as imagens das peças com redimensionamento dinâmico
def load_images(square_size):
    pieces = {
        'r': 'rb.png', 'n': 'nb.png', 'b': 'bb.png', 'q': 'qb.png', 'k': 'kb.png', 'p': 'pb.png',
        'R': 'rw.png', 'N': 'nw.png', 'B': 'bw.png', 'Q': 'qw.png', 'K': 'kw.png', 'P': 'pw.png'
    }
    images = {}
    for piece, filename in pieces.items():
        image = pygame.image.load(f'images/{filename}')
        images[piece] = pygame.transform.smoothscale(image, (square_size, square_size))
    return images

# Desenha o tabuleiro e as etiquetas
def draw_board(screen, board, images, font, board_size, square_size, offset):
    colors = [pygame.Color("white"), pygame.Color("gray")]

    for r in range(8):
        for c in range(8):
            color = colors[(r + c) % 2]
            square_rect = pygame.Rect(c * square_size + offset, r * square_size + offset, square_size, square_size)
            pygame.draw.rect(screen, color, square_rect)

            # Coloca a peça centralizada no quadrado
            piece = board.piece_at(chess.square(c, 7 - r))
            if piece:
                piece_img = images[piece.symbol()]
                piece_rect = piece_img.get_rect(center=square_rect.center)
                screen.blit(piece_img, piece_rect)

    # Desenha letras e números
    labels = 'abcdefgh'
    for i in range(8):
        label = font.render(labels[i], True, WHITE)
        screen.blit(label, ((i + 1) * square_size - square_size // 2 + offset, board_size + offset + 10))
        
        label = font.render(str(8 - i), True, WHITE)
        screen.blit(label, (offset - 30, (i + 1) * square_size - square_size // 2 + offset))

# Função principal do jogo
def main():
    board = chess.Board()
    running = True
    clock = pygame.time.Clock()
    
    # Fontes para texto
    fontCoordinates = pygame.font.Font(None, 36)
    fontTextBox = pygame.font.Font(None, 20)

    # Parâmetros dinâmicos
    screen = pygame.display.set_mode((840, 880), pygame.RESIZABLE)
    input_text = ''
    active = False
    message = ''

    # Caixa de texto na parte inferior
    input_height = 25  # Altura da caixa de entrada de texto

    while running:
        screen_width, screen_height = screen.get_size()
        
        # Calcula o tamanho do tabuleiro considerando a margem para coordenadas
        board_size = min(screen_width, screen_height - input_height - 100)
        square_size = board_size // 8
        offset = (screen_width - board_size) // 2

        images = load_images(square_size)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        move = input_text
                        try:
                            board.push_san(move)  # Move do jogador
                            stockfish.set_fen_position(board.fen())  # Atualiza o Stockfish
                            ai_move = stockfish.get_best_move()  # Move da IA
                            if ai_move:
                                board.push_uci(ai_move)
                            message = ''
                        except ValueError:
                            message = 'Jogada inválida. Tente novamente.'
                        input_text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

        screen.fill(BLACK)
        draw_board(screen, board, images, fontCoordinates, board_size, square_size, offset)

        # Caixa de entrada de texto embaixo
        input_box = pygame.Rect(0, screen_height - input_height, screen_width, input_height)
        txt_surface = fontTextBox.render(input_text, True, WHITE)
        screen.fill(GRAY, input_box)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, WHITE, input_box, 1)

        # Mensagem de erro
        msg_surface = fontTextBox.render(message, True, RED)
        screen.blit(msg_surface, (10, screen_height - input_height - 30))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
