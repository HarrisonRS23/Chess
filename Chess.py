import pygame
import os

"""
TODO: 
- Add checking the king
- Add checkmates 
- Add en passant 
- Add promotions
- Add draws
- Add stalemate
- Add resigning/reset
- Add sidebar of some sort
- Finish sound effects

"""

class ChessSprite(pygame.sprite.Sprite):
    def __init__(self, board_rect, i, j, image, color, piece_type):
        super().__init__()
        self.board = board_rect
        self.image = image
        self.color = color
        self.col = i
        self.row = j
        self.clicked = False
        self.piece_type = piece_type
        self.set_pos(i, j)
        if piece_type == 'r':
            self.has_moved = False
        if piece_type == 'k':
            self.has_moved = False

    def set_pos(self, i, j):
        # Clear position of old piece
        board_state[self.col][self.row] = None

        self.col = i
        self.row = j
        x = self.board.left + self.board.width // 8 * i + self.board.width // 16
        y = self.board.top + self.board.height // 8 * (7 - j) + self.board.height // 16
        self.rect = self.image.get_rect(center=(x, y))

    def was_clicked(self, event):
        return self.rect.collidepoint(event.pos)


def execute_move(sprite, dst_col, dst_row):

    # Kill piece 
    killed = False
    if(board_state[dst_col][dst_row] is not None):
        board_state[dst_col][dst_row] = None
        kill_piece(dst_col,dst_row)
        killed = True

    # TODO: Check if Promoting

    row = 0 if sprite.color == 0 else 7

    if(sprite.piece_type == 'k' and not sprite.has_moved):
        if((dst_col,dst_row) == (6,row)):
            castled_short(sprite)
            sprite.has_moved = True
            return

        elif ((dst_col,dst_row) == (2,row)):
            castled_long(sprite)
            sprite.has_moved = True
            return

    sprite.set_pos(dst_col,dst_row)

    # Cannot Castle if moved
    if(sprite.piece_type == 'k' or sprite.piece_type == 'r'):
        sprite.has_moved = True


    if not killed:
        move_sound.play()

    # TODO: Add case to check if the King is in check

    # write the moved piece into its new square
    board_state[dst_col][dst_row] = (sprite.color, sprite.piece_type, sprite)

    global current_turn
    #if current_turn == 0:
        #current_turn = 1
   # else:
       #current_turn = 0

    global selected_piece
    selected_piece = None
    print_chess_board()
    

def castled_short(sprite):

    castle_sound.play()
    row = 0 if sprite.color == 0 else 7

    # Move King
    sprite.set_pos(6,row)
    board_state[6][row] = (sprite.color, sprite.piece_type, sprite)
    # Move Rook
    rook = board_state[7][row][2]
    rook.set_pos(5,row)
    board_state[5][row] = (rook.color, rook.piece_type, rook)


def castled_long(sprite):

    castle_sound.play()
    row = 0 if sprite.color == 0 else 7

    # Move King
    sprite.set_pos(2,row)
    board_state[2][row] = (sprite.color, sprite.piece_type, sprite)
    # Move Rook
    rook = board_state[0][row][2]
    rook.set_pos(3,row)
    board_state[3][row] = (rook.color, rook.piece_type, rook)


def kill_piece(col, row):
    for sprite in group:
        if sprite.col == col and sprite.row == row:
            sprite.kill()
            capture_sound.play()

def get_valid_moves(sprite):
    piece_type = sprite.piece_type

    if piece_type == 'p':
        return get_pawn_moves(sprite)
    elif piece_type == 'b':
        return get_bishop_moves(sprite)
    elif piece_type == 'n':
        return get_knight_moves(sprite)
    elif piece_type == 'r':
        return get_rook_moves(sprite)
    elif piece_type == 'q':
        return get_queen_moves(sprite)
    elif piece_type == 'k':
        return get_king_moves(sprite)

    return []

def get_pawn_moves(sprite):

    valid_moves = []

    direction = 1 if sprite.color == 0 else -1
    start_row = 1 if sprite.color == 0 else 6

    # TODO: Fix end of the board after fixing promotion 

    # One step forward
    if board_state[sprite.col][sprite.row + direction] is None:
        valid_moves.append((sprite.col, sprite.row + direction))

        # Two steps from starting row
        if sprite.row == start_row and \
        board_state[sprite.col][sprite.row + 2 * direction] is None:
            valid_moves.append((sprite.col, sprite.row + 2 * direction))
    
    # Diagonal takes

    if sprite.col + 1 < 8 and board_state[sprite.col + 1][sprite.row + direction] is not None:
        valid_moves.append((sprite.col + 1,sprite.row + direction))
    if sprite.col - 1 >= 0 and board_state[sprite.col - 1][sprite.row + direction] is not None:
        valid_moves.append((sprite.col - 1,sprite.row + direction))

    # En-passant (Implement Later)

    return valid_moves

def get_knight_moves(sprite):

    x0 = sprite.col
    y0 = sprite.row

    valid_moves = []

    deltas = [(-2, -1), (-2, +1), (+2, -1), (+2, +1), (-1, -2), (-1, +2), (+1, -2), (+1, +2)]

    for (x, y) in deltas:
        xCandidate = x0 + x
        yCandidate = y0 + y
        if 0 <= xCandidate < 8 and 0 <= yCandidate < 8:
            valid_moves.append((xCandidate, yCandidate))

    return valid_moves

def get_rook_moves(sprite):
    valid_moves = []

    x = sprite.col
    y = sprite.row

    # move in up motion
    for y_up in range(y + 1, 8):
        if board_state[x][y_up] is not None:
            if board_state[x][y_up][0] != sprite.color:  # enemy piece, can capture
                valid_moves.append((x, y_up))
            break  # either way, stop here
        valid_moves.append((x, y_up))

    # move in down motion
    for y_up in range(y - 1, -1, -1):
        if board_state[x][y_up] is not None:
            if board_state[x][y_up][0] != sprite.color:  # enemy piece, can capture
                valid_moves.append((x, y_up))
            break  # either way, stop here
        valid_moves.append((x, y_up))

    # move in right motion
    for x_right in range(x + 1, 8):
        if board_state[x_right][y] is not None:
            if board_state[x_right][y][0] != sprite.color:  # enemy piece, can capture
                valid_moves.append((x_right, y))
            break  # either way, stop here
        valid_moves.append((x_right, y))


    for x_left in range(x - 1, -1, -1):
        if board_state[x_left][y] is not None:
            if board_state[x_left][y][0] != sprite.color:  # enemy piece, can capture
                valid_moves.append((x_left, y))
            break  # either way, stop here
        valid_moves.append((x_left, y))

    return valid_moves

def get_bishop_moves(sprite):
    valid_moves = []

    x = sprite.col
    y = sprite.row


    # move in up right
    for n in range(1, 8):
        if 0 <= x+n < 8 and 0 <= y+n < 8:
            if board_state[x + n][y + n] is not None:
                if board_state[x+n][y+n][0] != sprite.color:  # enemy piece, can capture
                    valid_moves.append((x+n, y+n))
                break  # either way, stop here
            valid_moves.append((x+n, y+n))

    # move in up left motion
    for n in range(1, 8):
        if 0 <= x-n < 8 and 0 <= y+n < 8:
            if board_state[x - n][y + n] is not None:
                if board_state[x-n][y+n][0] != sprite.color:  # enemy piece, can capture
                    valid_moves.append((x-n, y+n))
                break  # either way, stop here
            valid_moves.append((x-n, y+n))

    
    # move in down right
    for n in range(1, 8):
        if 0 <= x+n < 8 and 0 <= y-n < 8:
            if board_state[x + n][y - n] is not None:
                if board_state[x+n][y-n][0] != sprite.color:  # enemy piece, can capture
                    valid_moves.append((x+n, y-n))
                break  # either way, stop here
            valid_moves.append((x+n, y-n))

    # move in down left
    for n in range(1, 8):
        if 0 <= x-n < 8 and 0 <= y-n < 8:
            if board_state[x - n][y - n] is not None:
                if board_state[x-n][y-n][0] != sprite.color:  # enemy piece, can capture
                    valid_moves.append((x-n, y-n))
                break  # either way, stop here
            valid_moves.append((x-n, y-n))
    
    return valid_moves

def get_queen_moves(sprite):

    bishop_moves = get_bishop_moves(sprite)
    rook_moves = get_rook_moves(sprite)
    return bishop_moves + rook_moves

def get_king_moves(sprite):
    x0 = sprite.col
    y0 = sprite.row

    valid_moves = []

    deltas = [(0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1), (-1,0), (-1,1)]

    for (x, y) in deltas:
        xCandidate = x0 + x
        yCandidate = y0 + y
        if 0 <= xCandidate < 8 and 0 <= yCandidate < 8:
            valid_moves.append((xCandidate, yCandidate))

    # Check Castling 

    if sprite.has_moved == False:
       
        row = 0 if sprite.color == 0 else 7

        print(can_castle_short())
        print(can_castle_long())

        if can_castle_short():
            valid_moves.append((6,row))
        if can_castle_long():
           valid_moves.append((2,row))

    return valid_moves

def can_castle_short():
    row = 0 if sprite.color == 0 else 7
     
    for i in range(2): 
        if board_state[5+i][row] is not None:
            return False
    if board_state[7][row] is not None and board_state[7][row][2].has_moved == False:
        return True

def can_castle_long():
    row = 0 if sprite.color == 0 else 7
     
    for i in range(3): 
        if board_state[3-i][row] is not None:
            return False
    if board_state[0][row] is not None and board_state[0][row][2].has_moved == False:
        return True

# TODO: Complete function
def king_in_check(sprite):
    print("is the king in check?")

# Function to pretty print chessboard for visualization purposes
def print_chess_board():
    print('    ', end=" ")
    for y in range(8):
        if y == 0:
            print('[' + str(y) + ']' ,end=" ")
        else:
            print('[' + str(y) + '] ' ,end=" ")

    print()

    for i in range(8):
        print('[' + str(i) + ']' ,end=" ")
        for j in range(8):
            cell = board_state[i][j]
            if cell is not None:
                if cell[0] == 0:
                    color = 'w'
                else:
                    color = 'b'
                print('(' + color + cell[1] + ')',end=" ")
            else:
                print('(  )',end=" ")

        print()
    print('\n')
            

# Constants
global selected_piece, valid_moves, current_turn
current_turn = 0
selected_piece = None
valid_moves = []

WIDTH, HEIGHT = 800, 800
DIMENSION = 8
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
GREEN, CREAM = (115, 149, 82), (235, 236, 208)
LIGHT_ORANGE = (186, 201, 73) # Select color
GRAY = (202, 203, 179) # Indicator for valid moves
cellSize = WIDTH // DIMENSION

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ChessBoard")
clock = pygame.time.Clock()
running = True

def draw_board(i,j):
    global valid_moves
    board = pygame.Surface((cellSize * DIMENSION, cellSize * DIMENSION))
    board.fill(CREAM)
    for x in range(DIMENSION):
        for y in range(DIMENSION):

            # Highlighted Piece uses the flip
            if x == i and y == (7 - j):
                pygame.draw.rect(board, LIGHT_ORANGE, (x * cellSize, y * cellSize, cellSize, cellSize))
            
            elif (x + y) % 2 == 0:
                pygame.draw.rect(board, GREEN, (x * cellSize, y * cellSize, cellSize, cellSize))

            my_rect = pygame.Rect(x * cellSize, y * cellSize, cellSize, cellSize)

            # Draw avaliable moves
            if (x,7-y) in valid_moves:

                center = my_rect.center

                if 0 <= x < 8 and 0 <= y < 8:
                    if board_state[x][7-y] is not None and board_state[x][7-y][0] != selected_piece.color: 
                        # enemy piece, can capture
                        pygame.draw.circle(board, GRAY, center, 49, 7)
                        continue
                
                if board_state[x][7-y] is not None and board_state[x][7-y][0] == selected_piece.color: 
                    continue
                else:
                    pygame.draw.circle(board, GRAY, center, 10)

               

    return board

board = draw_board(-1,-1)
board_rect = board.get_rect(topleft=(0, 0))

# Loading in pieces

def load_piece(color, name):
    path = os.path.join("Pieces", f"{color}{name}.png")
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(image, (cellSize, cellSize))

piece_names = ['k', 'q', 'r', 'b', 'n', 'p']
white_images = {name: load_piece("w", name) for name in piece_names}
black_images = {name: load_piece("b", name) for name in piece_names}

board_state = [[None] * 8 for _ in range(8)]
group = pygame.sprite.Group()

def add_piece(col, row, images, color, piece_type):
    sprite = ChessSprite(board_rect, col, row, images[piece_type], color, piece_type)
    group.add(sprite)
    board_state[col][row] = (color, piece_type, sprite)

back_rank = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
for i, fig in enumerate(back_rank):
    add_piece(i, 0, white_images, 0, fig)
    add_piece(i, 1, white_images, 0, 'p')
    add_piece(i, 7, black_images, 1, fig)
    add_piece(i, 6, black_images, 1, 'p')

font = pygame.font.SysFont(None, 36)

# Sound effects

pygame.mixer.init()
capture_sound = pygame.mixer.Sound('Effects/capture.mp3')
castle_sound = pygame.mixer.Sound('Effects/castle.mp3')
game_end_sound = pygame.mixer.Sound('Effects/game-end.mp3')
illegal_sound = pygame.mixer.Sound('Effects/illegal.mp3')
move_sound = pygame.mixer.Sound('Effects/move-self.mp3')


# Game Loop

while running:
    event_list = pygame.event.get()

    if selected_piece is not None:
        board = draw_board(selected_piece.col, selected_piece.row)

    for event in event_list:
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:     
                   

            if selected_piece is None:
                # Phase 1: select a friendly piece
                for sprite in group:
                    if sprite.was_clicked(event) and sprite.color == current_turn:
                        selected_piece = sprite
                        valid_moves = get_valid_moves(sprite)
                        break

            else:
                clicked_col = (event.pos[0] - board_rect.left) // cellSize
                clicked_row = 7 - (event.pos[1] - board_rect.top) // cellSize

                if board_state[clicked_col][clicked_row] is not None:
                    for sprite in group:
                        if sprite.was_clicked(event) and sprite.color == current_turn:
                            selected_piece = sprite
                            valid_moves = get_valid_moves(sprite)
                            break
                
                if (clicked_col, clicked_row) in valid_moves:
                    execute_move(selected_piece, clicked_col, clicked_row)
                    selected_piece = None
                    valid_moves = []
                    board = draw_board(-1,-1)
                else:

                    # TODO: Change this to only illegal moves in check
                    if board_state[clicked_col][clicked_row] is None:
                        illegal_sound.play()


                    selected_piece = None
                    valid_moves = []
                    board = draw_board(-1,-1)
                    
                    for sprite in group:
                        if sprite.was_clicked(event) and sprite.color == current_turn:
                            selected_piece = sprite
                            valid_moves = get_valid_moves(sprite)
                            break

    screen.fill(BLACK)
    screen.blit(board, board_rect)

    group.draw(screen)

    label = font.render("White's Turn" if current_turn == 0 else "Black's Turn", True, WHITE)
    screen.blit(label, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()