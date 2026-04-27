import pygame
import os

"""
TODO: 
- Specify why the game ended
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
        if piece_type == 'p':
            self.enpassant = False
            self.enpassant_col = -1

    def set_pos(self, i, j):
        board_state[self.col][self.row] = None
        self.col = i
        self.row = j
        x = self.board.left + self.board.width // 8 * i + self.board.width // 16
        y = self.board.top + self.board.height // 8 * (7 - j) + self.board.height // 16
        self.rect = self.image.get_rect(center=(x, y))

    def was_clicked(self, event):
        return self.rect.collidepoint(event.pos)


def execute_move(sprite, dst_col, dst_row):

    # Save state and simulate move for check validation
    original_src = board_state[sprite.col][sprite.row]
    original_dst = board_state[dst_col][dst_row]
    old_col, old_row = sprite.col, sprite.row

    board_state[sprite.col][sprite.row] = None
    board_state[dst_col][dst_row] = (sprite.color, sprite.piece_type, sprite)
    sprite.col, sprite.row = dst_col, dst_row

    in_check = king_in_check(find_king_by_color(current_turn), board_state)

    # Restore everything
    sprite.col, sprite.row = old_col, old_row
    board_state[old_col][old_row] = original_src
    board_state[dst_col][dst_row] = original_dst

    if in_check:
        illegal_sound.play()
        return

    # Kill piece
    killed = False
    if board_state[dst_col][dst_row] is not None:
        board_state[dst_col][dst_row] = None
        kill_piece(dst_col, dst_row)
        killed = True

    row = 0 if sprite.color == 0 else 7

    # Add check to see if rook has moved
    if sprite.piece_type == 'k' and not sprite.has_moved:
        if (dst_col, dst_row) == (6, row):
            castled_short(sprite)
            sprite.has_moved = True
            switch_turns()
            return
        elif (dst_col, dst_row) == (2, row):
            castled_long(sprite)
            sprite.has_moved = True
            switch_turns()
            return
        
    original_row = sprite.row

    # En passant capture: destination square is empty but we're capturing diagonally
    is_enpassant = (
        sprite.piece_type == 'p'
        and dst_col != sprite.col
        and board_state[dst_col][dst_row] is None
    )
    if is_enpassant:
        captured_row = sprite.row  # the captured pawn is still on the moving pawn's row
        board_state[dst_col][captured_row] = None
        kill_piece(dst_col, captured_row)
        killed = True

    sprite.set_pos(dst_col, dst_row)

    if sprite.piece_type == 'k' or sprite.piece_type == 'r':
        sprite.has_moved = True

    promote_row = 0 if sprite.color == 1 else 7

    if(sprite.piece_type == 'p' and sprite.row == promote_row):
        global show_popup, popup_type, promoting_pawn
        show_popup = True
        popup_type = 'promotion'
        promoting_pawn = sprite
        # Sound and turn switch happen after promotion choice, so return early
        return
        

    # Write the moved piece into its new square
    board_state[dst_col][dst_row] = (sprite.color, sprite.piece_type, sprite)

    # Play appropriate sound
    opponent_color = 1 - current_turn
    opponent_king = find_king_by_color(opponent_color)

    if king_in_check(opponent_king, board_state):
        check_sound.play()
    elif killed:
        capture_sound.play()
    else:
        move_sound.play()

    if is_draw():
        game_over(False)

    if sprite.piece_type == 'p' and abs(original_row - dst_row) == 2:
        check_enpassant(dst_col, dst_row, sprite.color)

    switch_turns()

def switch_turns():

    global current_turn
    current_turn = 1 - current_turn
    global selected_piece
    selected_piece = None
    print_chess_board()

    # Clear en passant for the side that just moved — their window has now closed
    for i in range(8):
        for j in range(8):
            cell = board_state[i][j]
            # clears the previous player's flags (they missed their window)
            if cell and cell[0] == (1 - current_turn) and cell[1] == 'p':                
                cell[2].enpassant = False

    is_checkmate() # game_over is handled internally for both outcomes

def castled_short(sprite):
    castle_sound.play()
    row = 0 if sprite.color == 0 else 7
    sprite.set_pos(6, row)
    board_state[6][row] = (sprite.color, sprite.piece_type, sprite)
    rook = board_state[7][row][2]
    rook.set_pos(5, row)
    board_state[5][row] = (rook.color, rook.piece_type, rook)

def castled_long(sprite):
    castle_sound.play()
    row = 0 if sprite.color == 0 else 7
    sprite.set_pos(2, row)
    board_state[2][row] = (sprite.color, sprite.piece_type, sprite)
    rook = board_state[0][row][2]
    rook.set_pos(3, row)
    board_state[3][row] = (rook.color, rook.piece_type, rook)

def kill_piece(col, row):
    for sprite in group:
        if sprite.col == col and sprite.row == row:
            if sprite.color == 0:
                killed_white_pieces.append(sprite)
            else:
                killed_black_pieces.append(sprite)
            sprite.kill()

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

    if board_state[sprite.col][sprite.row + direction] is None:
        valid_moves.append((sprite.col, sprite.row + direction))
        if sprite.row == start_row and board_state[sprite.col][sprite.row + 2 * direction] is None:
            valid_moves.append((sprite.col, sprite.row + 2 * direction))

    if sprite.col + 1 < 8 and board_state[sprite.col + 1][sprite.row + direction] is not None \
            and board_state[sprite.col + 1][sprite.row + direction][0] != sprite.color:
        valid_moves.append((sprite.col + 1, sprite.row + direction))
    if sprite.col - 1 >= 0 and board_state[sprite.col - 1][sprite.row + direction] is not None \
            and board_state[sprite.col - 1][sprite.row + direction][0] != sprite.color:
        valid_moves.append((sprite.col - 1, sprite.row + direction))

    # En-passant (Implement Later)

    # generate the move, don't touch the flag here
    if sprite.enpassant:
        dest_row = sprite.row + direction  # one step forward in moving direction
        valid_moves.append((sprite.enpassant_col, dest_row))
        


    return valid_moves

def get_knight_moves(sprite):
    x0, y0 = sprite.col, sprite.row
    valid_moves = []
    deltas = [(-2, -1), (-2, +1), (+2, -1), (+2, +1), (-1, -2), (-1, +2), (+1, -2), (+1, +2)]
    for (x, y) in deltas:
        xc, yc = x0 + x, y0 + y
        if 0 <= xc < 8 and 0 <= yc < 8:
            if board_state[xc][yc] is None or board_state[xc][yc][0] != sprite.color:
                valid_moves.append((xc, yc))
    return valid_moves

def get_rook_moves(sprite):
    valid_moves = []
    x, y = sprite.col, sprite.row

    for y_up in range(y + 1, 8):
        if board_state[x][y_up] is not None:
            if board_state[x][y_up][0] != sprite.color:
                valid_moves.append((x, y_up))
            break
        valid_moves.append((x, y_up))

    for y_down in range(y - 1, -1, -1):
        if board_state[x][y_down] is not None:
            if board_state[x][y_down][0] != sprite.color:
                valid_moves.append((x, y_down))
            break
        valid_moves.append((x, y_down))

    for x_right in range(x + 1, 8):
        if board_state[x_right][y] is not None:
            if board_state[x_right][y][0] != sprite.color:
                valid_moves.append((x_right, y))
            break
        valid_moves.append((x_right, y))

    for x_left in range(x - 1, -1, -1):
        if board_state[x_left][y] is not None:
            if board_state[x_left][y][0] != sprite.color:
                valid_moves.append((x_left, y))
            break
        valid_moves.append((x_left, y))

    return valid_moves

def get_bishop_moves(sprite):
    valid_moves = []
    x, y = sprite.col, sprite.row

    for n in range(1, 8):
        if 0 <= x+n < 8 and 0 <= y+n < 8:
            if board_state[x+n][y+n] is not None:
                if board_state[x+n][y+n][0] != sprite.color:
                    valid_moves.append((x+n, y+n))
                break
            valid_moves.append((x+n, y+n))

    for n in range(1, 8):
        if 0 <= x-n < 8 and 0 <= y+n < 8:
            if board_state[x-n][y+n] is not None:
                if board_state[x-n][y+n][0] != sprite.color:
                    valid_moves.append((x-n, y+n))
                break
            valid_moves.append((x-n, y+n))

    for n in range(1, 8):
        if 0 <= x+n < 8 and 0 <= y-n < 8:
            if board_state[x+n][y-n] is not None:
                if board_state[x+n][y-n][0] != sprite.color:
                    valid_moves.append((x+n, y-n))
                break
            valid_moves.append((x+n, y-n))

    for n in range(1, 8):
        if 0 <= x-n < 8 and 0 <= y-n < 8:
            if board_state[x-n][y-n] is not None:
                if board_state[x-n][y-n][0] != sprite.color:
                    valid_moves.append((x-n, y-n))
                break
            valid_moves.append((x-n, y-n))

    return valid_moves

def get_queen_moves(sprite):
    return get_bishop_moves(sprite) + get_rook_moves(sprite)

def get_king_moves(sprite):
    x0, y0 = sprite.col, sprite.row
    valid_moves = []
    deltas = [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]

    for (x, y) in deltas:
        xc, yc = x0 + x, y0 + y
        if 0 <= xc < 8 and 0 <= yc < 8:
            if board_state[xc][yc] is None or board_state[xc][yc][0] != sprite.color:
                # Simulate move and check for check
                original = board_state[xc][yc]
                board_state[x0][y0] = None
                board_state[xc][yc] = (sprite.color, sprite.piece_type, sprite)
                sprite.col, sprite.row = xc, yc

                in_check = king_in_check(sprite, board_state)

                sprite.col, sprite.row = x0, y0
                board_state[x0][y0] = (sprite.color, sprite.piece_type, sprite)
                board_state[xc][yc] = original

                if not in_check:
                    valid_moves.append((xc, yc))

    if not sprite.has_moved:
        row = 0 if sprite.color == 0 else 7
        if can_castle_short(sprite):
            valid_moves.append((6, row))
        if can_castle_long(sprite):
            valid_moves.append((2, row))

    return valid_moves

def can_castle_short(sprite):
    row = 0 if sprite.color == 0 else 7
    for i in range(2):
        if board_state[5+i][row] is not None:
            return False
    cell = board_state[7][row]
    if cell is not None and cell[0] == sprite.color and board_state[7][row][2].has_moved == False:
        return True
    return False

def can_castle_long(sprite):
    row = 0 if sprite.color == 0 else 7
    for i in range(3):
        if board_state[3-i][row] is not None:
            return False
    cell = board_state[0][row]
    if cell is not None and cell[0] == sprite.color and board_state[0][row][2].has_moved == False:
        return True
    return False

def find_king_by_color(color):
    for i in range(8):
        for j in range(8):
            cell = board_state[i][j]
            if cell is not None and cell[0] == color and cell[1] == 'k':
                return cell[2]

def king_in_check(sprite, board):
    x, y = sprite.col, sprite.row
    board_state = board

    # Rook / Queen (straight lines)
    for y_up in range(y + 1, 8):
        if board_state[x][y_up] is not None:
            if board_state[x][y_up][0] != sprite.color:
                if board_state[x][y_up][1] in ('q', 'r'):
                    return True
            break

    for y_down in range(y - 1, -1, -1):
        if board_state[x][y_down] is not None:
            if board_state[x][y_down][0] != sprite.color:
                if board_state[x][y_down][1] in ('q', 'r'):
                    return True
            break

    for x_right in range(x + 1, 8):
        if board_state[x_right][y] is not None:
            if board_state[x_right][y][0] != sprite.color:
                if board_state[x_right][y][1] in ('q', 'r'):
                    return True
            break

    for x_left in range(x - 1, -1, -1):
        if board_state[x_left][y] is not None:
            if board_state[x_left][y][0] != sprite.color:
                if board_state[x_left][y][1] in ('q', 'r'):
                    return True
            break

    # Bishop / Queen (diagonals)
    for n in range(1, 8):
        if 0 <= x+n < 8 and 0 <= y+n < 8:
            if board_state[x+n][y+n] is not None:
                if board_state[x+n][y+n][0] != sprite.color:
                    if board_state[x+n][y+n][1] in ('q', 'b'):
                        return True
                break

    for n in range(1, 8):
        if 0 <= x-n < 8 and 0 <= y+n < 8:
            if board_state[x-n][y+n] is not None:
                if board_state[x-n][y+n][0] != sprite.color:
                    if board_state[x-n][y+n][1] in ('q', 'b'):
                        return True
                break

    for n in range(1, 8):
        if 0 <= x+n < 8 and 0 <= y-n < 8:
            if board_state[x+n][y-n] is not None:
                if board_state[x+n][y-n][0] != sprite.color:
                    if board_state[x+n][y-n][1] in ('q', 'b'):
                        return True
                break

    for n in range(1, 8):
        if 0 <= x-n < 8 and 0 <= y-n < 8:
            if board_state[x-n][y-n] is not None:
                if board_state[x-n][y-n][0] != sprite.color:
                    if board_state[x-n][y-n][1] in ('q', 'b'):
                        return True
                break

    # Knight
    for (dx, dy) in [(-2,-1),(-2,+1),(+2,-1),(+2,+1),(-1,-2),(-1,+2),(+1,-2),(+1,+2)]:
        xc, yc = x + dx, y + dy
        if 0 <= xc < 8 and 0 <= yc < 8:
            if board_state[xc][yc] is not None and board_state[xc][yc][0] != sprite.color:
                if board_state[xc][yc][1] == 'n':
                    return True

    # Pawn
    pawn_direction = 1 if sprite.color == 0 else -1
    for dx in [-1, 1]:
        px = x + dx
        py = y + pawn_direction
        if 0 <= px < 8 and 0 <= py < 8:
            if board_state[px][py] is not None and board_state[px][py][0] != sprite.color:
                if board_state[px][py][1] == 'p':
                    return True

    # Enemy King (prevent kings from being adjacent)
    for (dx, dy) in [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]:
        xc, yc = x + dx, y + dy
        if 0 <= xc < 8 and 0 <= yc < 8:
            if board_state[xc][yc] is not None and board_state[xc][yc][0] != sprite.color:
                if board_state[xc][yc][1] == 'k':
                    return True

    return False

def print_chess_board():
    print('    ', end=" ")
    for y in range(8):
        print('[' + str(y) + (']' if y == 0 else '] '), end=" ")
    print()
    for i in range(8):
        print('[' + str(i) + ']', end=" ")
        for j in range(8):
            cell = board_state[i][j]
            if cell is not None:
                color = 'w' if cell[0] == 0 else 'b'
                print('(' + color + cell[1] + ')', end=" ")
            else:
                print('(  )', end=" ")
        print()
    print('\n')

def draw_promotion_popup(color):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # semi-transparent dark overlay
    screen.blit(overlay, (0, 0))

    popup_w, popup_h = 400, 120
    popup_x = WIDTH // 2 - popup_w // 2
    popup_y = HEIGHT // 2 - popup_h // 2
    pygame.draw.rect(screen, CREAM, (popup_x, popup_y, popup_w, popup_h), border_radius=10)
    pygame.draw.rect(screen, BLACK, (popup_x, popup_y, popup_w, popup_h), 2, border_radius=10)

    label = font.render("Choose promotion:", True, BLACK)
    screen.blit(label, (popup_x + 10, popup_y + 8))

    images = white_images if color == 0 else black_images
    pieces = ['q', 'r', 'b', 'n']
    rects = []
    for idx, piece in enumerate(pieces):
        rect = pygame.Rect(popup_x + 10 + idx * 95, popup_y + 40, 80, 70)
        pygame.draw.rect(screen, GREEN, rect, border_radius=6)
        screen.blit(pygame.transform.smoothscale(images[piece], (80, 70)), rect.topleft)
        rects.append((rect, piece))

    return rects

def is_checkmate():

    """
    Generate the list of pseudo-legal moves for the side to move. 
    By pseudo-legal, I mean don't bother to verify whether the generated move leaves that side's King in check. 
    Omitting this verification can save time validating moves that are never searched.

    For each move that is searched, validate that it doesn't leave the side to move in check.

    If every move leaves the King in check, then the side to move has either been mated or it's stalemate.

    If the side to move is currently in check, then it's mate. Otherwise it's stalemate.

    """

    if get_king_moves(find_king_by_color(current_turn)) != []:
        return False
    
    pseudo_legal = []
    
    for i in range(8):
        for j in range(8):
            cell = board_state[i][j]
            if cell is not None and cell[0] == current_turn:
                pseudo_legal.append((get_valid_moves(cell[2]), cell))

    for moves, cell in pseudo_legal:
        piece = cell[2]
        for move in list(moves):  # iterate over a copy when removing
            dst_col, dst_row = move
            original_src = board_state[piece.col][piece.row]
            original_dst = board_state[dst_col][dst_row]
            old_col, old_row = piece.col, piece.row

            board_state[piece.col][piece.row] = None
            board_state[dst_col][dst_row] = (piece.color, piece.piece_type, piece)
            piece.col, piece.row = dst_col, dst_row

            in_check = king_in_check(find_king_by_color(current_turn), board_state)

            piece.col, piece.row = old_col, old_row
            board_state[old_col][old_row] = original_src
            board_state[dst_col][dst_row] = original_dst

            if in_check:
                moves.remove(move)

    all_legal = [m for moves, cell in pseudo_legal for m in moves]
    if not all_legal:
        if king_in_check(find_king_by_color(current_turn), board_state):
            game_over(is_checkmate=True)
            return True
        else:
            game_over(is_checkmate=False)
            return True  # return True either way so switch_turns knows game ended

    return False

def game_over(is_checkmate):
    global game_over_flag, game_over_message
    game_over_flag = True
    game_end_sound.play()
    winner = 1 - current_turn
    if is_checkmate:
        game_over_message = "Checkmate! " + ("White" if winner == 0 else "Black") + " wins!"
    else:
        game_over_message = "It's a draw!"

def draw_game_over_popup():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    popup_w, popup_h = 400, 120
    popup_x = WIDTH // 2 - popup_w // 2
    popup_y = HEIGHT // 2 - popup_h // 2
    pygame.draw.rect(screen, CREAM, (popup_x, popup_y, popup_w, popup_h), border_radius=10)
    pygame.draw.rect(screen, BLACK, (popup_x, popup_y, popup_w, popup_h), 2, border_radius=10)

    label = font.render(game_over_message, True, BLACK)
    screen.blit(label, (popup_x + 20, popup_y + 20))

    restart_rect = pygame.Rect(popup_x + 120, popup_y + 60, 160, 40)
    pygame.draw.rect(screen, GREEN, restart_rect, border_radius=6)
    btn_label = font.render("Play Again", True, WHITE)
    screen.blit(btn_label, (restart_rect.x + 28, restart_rect.y + 10))

    return restart_rect

def is_draw():

    white_material, black_material = calculate_material()

    # Draws by insufficient material 

    # only kings left in game

    white_only_king = (white_material == 0)
    black_only_king = (black_material == 0)

    if white_only_king and black_only_king:
        print('Draw by: two kings')
        return True
    
    white_pieces = []
    black_pieces = []

    for i in range(8):
        for j in range(8):
            cell = board_state[i][j]
            if cell is not None:
                if cell[0] == 0:
                    white_pieces.append(cell[1])
                else:
                    black_pieces.append(cell[1])
           
    white_only_minor = False
    black_only_minor = False
    if white_material == 3:
        if 'p' not in white_pieces:
            white_only_minor = True
    if black_material == 3:
        if 'p' not in black_pieces:
            black_only_minor = True
    

    # Single minor piece e.g king vs king + bishop/knight
    if (white_only_king and black_only_minor) or (black_only_king and white_only_minor):
        print('draw by insufficient material: king vs minor piece')
        return True

    # Mirror minor piece e.g king + bishop/knight vs king + bishop/knight
    if white_only_minor and black_only_minor:
        print('draw by insufficient material: mirror minor piece ')
        return True
    
    # 2 knights vs king e.g king vs king + knight + knight

    if sorted(white_pieces) == ['k', 'n', 'n'] and black_material == 0:
        print("draw by insufficient material: king vs two knights")
        return True
    
    if sorted(black_pieces) == ['k', 'n', 'n'] and white_material == 0:
        print("draw by insufficient material: king vs two knights")
        return True
    
def check_enpassant(col, row, color):
    if col + 1 < 8 and board_state[col + 1][row] is not None \
            and board_state[col + 1][row][0] != color \
            and board_state[col + 1][row][1] == 'p':
        cell = board_state[col + 1][row]
        cell[2].enpassant = True
        cell[2].enpassant_col = col  # capture destination is the moved pawn's column

    if col - 1 >= 0 and board_state[col - 1][row] is not None \
            and board_state[col - 1][row][0] != color \
            and board_state[col - 1][row][1] == 'p':
        cell = board_state[col - 1][row]
        cell[2].enpassant = True
        cell[2].enpassant_col = col  # same — always col, not col±1

def reset_game():
    global board, killed_black_pieces, killed_white_pieces, side_panel
    global selected_piece, current_turn, valid_moves, board_state, group
    global show_popup, popup_type, promoting_pawn

    selected_piece = None
    current_turn = 0
    valid_moves = []
    show_popup = False
    popup_type = None
    promoting_pawn = None

    killed_black_pieces = []
    killed_white_pieces = []

    board_state = [[None] * 8 for _ in range(8)]
    group.empty()

    back_rank = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
    for i, fig in enumerate(back_rank):
        add_piece(i, 0, white_images, 0, fig)
        add_piece(i, 1, white_images, 0, 'p')
        add_piece(i, 7, black_images, 1, fig)
        add_piece(i, 6, black_images, 1, 'p')

    board = draw_board(-1, -1)
    side_panel = draw_side_panel()


# Constants 
global selected_piece, valid_moves, current_turn, board, killed_black_pieces, killed_white_pieces, side_panel
current_turn = 0
selected_piece = None
valid_moves = []
show_popup = False
popup_type = None   # 'promotion'
promoting_pawn = None
game_over_flag = False


WIDTH, HEIGHT = 800, 800
DIMENSION = 8
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
GREEN, CREAM = (115, 149, 82), (235, 236, 208)
LIGHT_ORANGE = (186, 201, 73)
GRAY = (202, 203, 179)
cellSize = WIDTH // DIMENSION

pygame.init()
screen = pygame.display.set_mode((WIDTH + 300, HEIGHT))
pygame.display.set_caption("ChessBoard")
clock = pygame.time.Clock()
running = True

def draw_board(i, j):
    global valid_moves
    board = pygame.Surface((cellSize * DIMENSION, cellSize * DIMENSION))
    board.fill(CREAM)
    for x in range(DIMENSION):
        for y in range(DIMENSION):
            if x == i and y == (7 - j):
                pygame.draw.rect(board, LIGHT_ORANGE, (x * cellSize, y * cellSize, cellSize, cellSize))
            elif (x + y) % 2 == 0:
                pygame.draw.rect(board, GREEN, (x * cellSize, y * cellSize, cellSize, cellSize))

            my_rect = pygame.Rect(x * cellSize, y * cellSize, cellSize, cellSize)

            if (x, 7-y) in valid_moves:
                center = my_rect.center  # ← move this up
                is_ep_target = (
                    selected_piece is not None
                    and selected_piece.piece_type == 'p'
                    and board_state[x][7-y] is None
                    and x != selected_piece.col
                )
                if is_ep_target:
                    pygame.draw.circle(board, GRAY, center, 49, 7)
                    continue
                if board_state[x][7-y] is not None and board_state[x][7-y][0] != selected_piece.color:
                    pygame.draw.circle(board, GRAY, center, 49, 7)
                    continue
                if board_state[x][7-y] is not None and board_state[x][7-y][0] == selected_piece.color:
                    continue
                else:
                    pygame.draw.circle(board, GRAY, center, 10)

    


    return board

board = draw_board(-1, -1)
board_rect = board.get_rect(topleft=(0, 0))

def load_piece(color, name):
    path = os.path.join("Pieces", f"{color}{name}.png")
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(image, (cellSize, cellSize))


piece_names = ['k', 'q', 'r', 'b', 'n', 'p']
white_images = {name: load_piece("w", name) for name in piece_names}
black_images = {name: load_piece("b", name) for name in piece_names}

global group
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

killed_black_pieces = []
killed_white_pieces = []

def calculate_material():

    piece_values = {'q': 9, 'r': 5, 'b': 3, 'n': 3, 'p': 1, 'k': 0}
    white_material = 0
    black_material = 0

    for i in range(8):
        for j in range(8):
            cell = board_state[i][j]
            if cell is not None:
                value = piece_values[cell[2].piece_type]
                if cell[0] == 0:
                    white_material += value 
                else:
                    black_material += value

    return white_material, black_material

def draw_side_panel():
    side_panel = pygame.Surface((400, 800))
    side_panel.fill(BLACK)

    restart_rect = pygame.Rect(60, 750, 160, 40)
    pygame.draw.rect(side_panel, WHITE, restart_rect, border_radius=6)
    btn_label = font.render("Play Again", True, BLACK)
    side_panel.blit(btn_label, (restart_rect.x + 28, restart_rect.y + 10))

    white_material, black_material = calculate_material()
    advantage = white_material - black_material

    # --- Black section (top half) ---
    black_label = font.render('Black', True, WHITE)
    side_panel.blit(black_label, (20, 20))

    # White pieces killed by black (shown under Black's label)
    for i, piece in enumerate(killed_white_pieces):
        x = 20 + (i % 8) * 28
        y = 50 + (i // 8) * 28
        side_panel.blit(pygame.transform.smoothscale(
            white_images[piece.piece_type], (25, 25)), (x, y))

    if advantage < 0:  # black is ahead
        adv_label = font.render(f'+{abs(advantage)}', True, WHITE)
        side_panel.blit(adv_label, (20, 110))


    # --- White section (bottom half) ---
    white_label = font.render('White', True, WHITE)
    side_panel.blit(white_label, (20, 400))

    # Black pieces killed by white (shown under White's label)
    for i, piece in enumerate(killed_black_pieces):
        x = 20 + (i % 8) * 28
        y = 430 + (i // 8) * 28
        side_panel.blit(pygame.transform.smoothscale(
            black_images[piece.piece_type], (25, 25)), (x, y))

    if advantage > 0:  # white is ahead
        adv_label = font.render(f'+{advantage}', True, WHITE)
        side_panel.blit(adv_label, (20, 490))

    return side_panel

side_panel = draw_side_panel()
side_panel_rect = side_panel.get_rect(topleft=(WIDTH, 0))

pygame.mixer.init()
capture_sound = pygame.mixer.Sound('Effects/capture.mp3')
castle_sound = pygame.mixer.Sound('Effects/castle.mp3')
game_end_sound = pygame.mixer.Sound('Effects/game-end.mp3')
illegal_sound = pygame.mixer.Sound('Effects/illegal.mp3')
move_sound = pygame.mixer.Sound('Effects/move-self.mp3')
check_sound = pygame.mixer.Sound('Effects/move-check.mp3')


# Game Loop
while running:
    event_list = pygame.event.get()

    promotion_rects = []

    for event in event_list:
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if show_popup and popup_type == 'promotion':
                # Click is consumed by the popup — check promotion_rects below
                pass

            if game_over_flag:
                pass  # ignore all clicks after game ends

            elif selected_piece is None:
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
                    board = draw_board(-1, -1)
                else:
                    if board_state[clicked_col][clicked_row] is None:
                        illegal_sound.play()
                    selected_piece = None
                    valid_moves = []
                    board = draw_board(-1, -1)
                    for sprite in group:
                        if sprite.was_clicked(event) and sprite.color == current_turn:
                            selected_piece = sprite
                            valid_moves = get_valid_moves(sprite)
                            break

    screen.fill(BLACK)

    if selected_piece is not None:
        board = draw_board(selected_piece.col, selected_piece.row)

    side_panel = draw_side_panel()
    screen.blit(board, board_rect)
    screen.blit(side_panel,side_panel_rect)
    group.draw(screen)

    label = font.render("White's Turn" if current_turn == 0 else "Black's Turn", True, WHITE)
    screen.blit(label, (10, 10))

    if show_popup and popup_type == 'promotion':
        promotion_rects = draw_promotion_popup(promoting_pawn.color)

        # Check for click on a promotion piece
        mouse = pygame.mouse.get_pressed()
        if mouse[0]:
            mouse_pos = pygame.mouse.get_pos()
            for rect, piece in promotion_rects:
                if rect.collidepoint(mouse_pos):
                    images = white_images if promoting_pawn.color == 0 else black_images
                    promoting_pawn.image = pygame.transform.smoothscale(images[piece], (cellSize, cellSize))
                    promoting_pawn.piece_type = piece
                    board_state[promoting_pawn.col][promoting_pawn.row] = (
                        promoting_pawn.color, piece, promoting_pawn
                    )
                    show_popup = False
                    popup_type = None

                    opponent_color = 1 - current_turn
                    opponent_king = find_king_by_color(opponent_color)
                    if king_in_check(opponent_king, board_state):
                        check_sound.play()
                    else:
                        move_sound.play()

                    switch_turns()
                    break

    # After the promotion popup block:
    if game_over_flag:
        restart_rect = draw_game_over_popup()
        mouse = pygame.mouse.get_pressed()
        if mouse[0]:
            if restart_rect.collidepoint(pygame.mouse.get_pos()):
                reset_game()
                game_over_flag = False
                

    restart_rect = pygame.Rect(WIDTH + 60, 750, 160, 40)
    mouse = pygame.mouse.get_pressed()
    if mouse[0]:
        if restart_rect.collidepoint(pygame.mouse.get_pos()):
            reset_game()
            game_over_flag = False  # ← needed if resetting after game over


    pygame.display.flip()
    clock.tick(60)

pygame.quit()