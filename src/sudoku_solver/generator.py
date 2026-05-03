from __future__ import annotations

import random

from sudoku_solver.board import Board, find_empty_cell, is_valid_placement
from sudoku_solver.config.settings import CLUES_BY_DIFFICULTY
from sudoku_solver.solver import count_solutions


def generate_puzzle(difficulty: str, rng: random.Random | None = None) -> Board:
    """Generate a valid Sudoku puzzle with a unique solution.

    Args:
        difficulty: One of "easy", "medium", "hard", "evil".
        rng: Optional seeded Random for reproducibility in tests.

    Returns:
        Board with givens mask marking clue cells; all other cells are 0.
    """
    if rng is None:
        rng = random.Random()

    target_clues = CLUES_BY_DIFFICULTY[difficulty]

    board = Board.empty()
    _fill_grid(board, rng)
    _dig_holes(board, target_clues, rng)
    return board


def _fill_grid(board: Board, rng: random.Random) -> bool:
    """Recursively fill an empty board with a valid complete solution.

    Uses backtracking with shuffled digit order for randomness.
    """
    cell = find_empty_cell(board)
    if cell is None:
        return True

    row, col = cell
    digits = list(range(1, 10))
    rng.shuffle(digits)

    for digit in digits:
        if is_valid_placement(board, row, col, digit):
            board.set(row, col, digit)
            if _fill_grid(board, rng):
                return True
            board.set(row, col, 0)

    return False


def _dig_holes(board: Board, target_clues: int, rng: random.Random) -> None:
    """Remove digits from a filled board until target_clues remain.

    Each removal is only accepted if the board retains a unique solution.
    Cells are shuffled once; a cell is skipped permanently after one failed
    removal attempt to bound runtime on harder difficulties.
    """
    cells = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(cells)

    # Mark all filled cells as givens before digging
    for r in range(9):
        for c in range(9):
            board.givens[r][c] = True

    for row, col in cells:
        if _count_givens(board) <= target_clues:
            break

        saved = board.get(row, col)
        board.set(row, col, 0)
        board.givens[row][col] = False

        if count_solutions(board, limit=2) != 1:
            # Removal breaks uniqueness — restore
            board.set(row, col, saved)
            board.givens[row][col] = True


def _count_givens(board: Board) -> int:
    """Return the number of filled (non-zero) cells in the board."""
    return sum(1 for r in range(9) for c in range(9) if board.get(r, c) != 0)
