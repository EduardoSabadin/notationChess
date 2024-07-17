import pygame
import chess

# Inicializa pygame
pygame.init()

# Define as cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
RED = (255, 0, 0)

# Define o tamanho da janela
size = width, height = 840, 880
screen = pygame.display.set_mode(size)

# Carrega as imagens das peças
def load_images():
    pieces = {
        'r': 'rb.png', 'n': 'nb.png', 'b': 'bb.png', 'q': 'qb.png', 'k': 'kb.png', 'p': 'pb.png',
        'R': 'rw.png', 'N': 'nw.png', 'B': 'bw.png', 'Q': 'qw.png', 'K': 'kw.png', 'P': 'pw.png'
    }
    images = {}
    for piece, filename in pieces.items():
        images[piece] = pygame.image.load(f'images/{filename}')
    return images

# Desenha o tabuleiro e as etiquetas
def draw_board(screen, board, images, font):
    colors = [pygame.Color("white"), pygame.Color("gray")]
    offset = 0  # Tamanho da faixa preta
    board_size = 8 * 100
    for r in range(8):
        for c in range(8):
            color = colors[(r + c) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(c * 100 + offset, r * 100 + offset, 100, 100))
            piece = board.piece_at(chess.square(c, 7 - r))
            if piece:
                screen.blit(images[piece.symbol()], pygame.Rect(c * 100 + offset, r * 100 + offset, 100, 100))
    
    # Desenha as letras e números
    labels = 'abcdefgh'
    for i in range(8):
        label = font.render(labels[i], True, WHITE)
        screen.blit(label, ((i + 1) * 100 - 50 + offset, board_size + offset + 10))
        screen.blit(label, ((i + 1) * 100 - 50 + offset, offset - 30))
        
        label = font.render(str(8 - i), True, WHITE)
        screen.blit(label, (offset - 30, (i + 1) * 100 - 50 + offset))
        screen.blit(label, (board_size + offset + 10, (i + 1) * 100 - 50 + offset))

# Função principal do jogo
def main():
    board = chess.Board()
    images = load_images()
    clock = pygame.time.Clock()
    running = True

    font = pygame.font.Font(None, 36)
    input_box = pygame.Rect(5, 840, 780, 30)
    input_text = ''
    active = False
    message = ''

    while running:
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
                            board.push_san(move)
                            message = ''
                        except ValueError:
                            message = 'Jogada inválida. Tente novamente.'
                        input_text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

        screen.fill(pygame.Color("black"))
        draw_board(screen, board, images, font)

        # Desenha a entrada de texto
        txt_surface = font.render(input_text, True, WHITE)
        screen.fill(GRAY, input_box)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, WHITE, input_box, 2)

        # Desenha a mensagem
        msg_surface = font.render(message, True, RED)
        screen.blit(msg_surface, (10, 850))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
