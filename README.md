# Chess Game

A fully functional chess game built with Python and Pygame, featuring complete chess rules, piece movement validation, and check/checkmate detection.

## Features

- **Complete Chess Rules**: Full implementation of standard chess rules including:
  - All piece movements (pawns, rooks, knights, bishops, queens, kings)
  - Castling
  - En passant
  - Pawn promotion
  - Check and checkmate detection
  
- **GUI**: Interactive board interface with Pygame
- **Move Validation**: Ensures all moves are legal according to chess rules
- **Game State Tracking**: Tracks piece positions, move history, and game status

## Requirements

- Python 3.x
- Pygame

## Installation

1. Install Python dependencies:
```bash
pip install pygame
```

2. Navigate to the Chess directory:
```bash
cd /Users/shivanikadirgamarajah/todolist/Chess
```

## Running the Game

Start the game with:
```bash
python3 Chess.py
```

## How to Play

- **Click** on a piece to select it
- **Click** on a highlighted square to move the piece
- The game will validate all moves according to standard chess rules
- The game detects and announces check and checkmate conditions

## Project Structure

- **Chess.py** - Main game file with core chess logic and sprite management
- **Game.py-Archive** - Archived game version
- **Pieces/** - Piece asset files and related data
- **Effects/** - Visual effects and animations

## Controls

- **Mouse click** to select and move pieces
- **F key** to toggle fullscreen mode
- Follow on-screen prompts for game actions

## Future Improvements

- [ ] Specify why the game ended (in progress)
- [ ] Game history/move replay
- [ ] Undo moves
- [ ] Save/load game state
- [ ] AI opponent
- [ ] Multiple game themes

## License

This project is open source and available in this repository.
