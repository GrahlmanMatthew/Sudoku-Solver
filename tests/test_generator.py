import random

import pytest

from sudoku_solver.board import Board
from sudoku_solver.generator import generate_puzzle
from sudoku_solver.solver import count_solutions


def _check_no_row_col_box_conflicts(board: Board) -> bool:
    """Return True if all given cells satisfy Sudoku constraints."""
    for r in range(9):
        row_digits = [board.get(r, c) for c in range(9) if board.get(r, c) != 0]
        if len(row_digits) != len(set(row_digits)):
            return False
    for c in range(9):
        col_digits = [board.get(r, c) for r in range(9) if board.get(r, c) != 0]
        if len(col_digits) != len(set(col_digits)):
            return False
    for box_r in range(3):
        for box_c in range(3):
            digits = [
                board.get(box_r * 3 + dr, box_c * 3 + dc)
                for dr in range(3)
                for dc in range(3)
                if board.get(box_r * 3 + dr, box_c * 3 + dc) != 0
            ]
            if len(digits) != len(set(digits)):
                return False
    return True


@pytest.fixture
def rng() -> random.Random:
    return random.Random(42)


def test_generate_easy_clue_count(rng: random.Random) -> None:
    board = generate_puzzle("easy", rng)
    clues = sum(1 for r in range(9) for c in range(9) if board.get(r, c) != 0)
    assert 44 <= clues <= 50


def test_generate_medium_clue_count(rng: random.Random) -> None:
    board = generate_puzzle("medium", rng)
    clues = sum(1 for r in range(9) for c in range(9) if board.get(r, c) != 0)
    assert 37 <= clues <= 43


def test_generate_hard_clue_count(rng: random.Random) -> None:
    board = generate_puzzle("hard", rng)
    clues = sum(1 for r in range(9) for c in range(9) if board.get(r, c) != 0)
    assert 27 <= clues <= 36


def test_generate_unique_solution(rng: random.Random) -> None:
    board = generate_puzzle("medium", rng)
    assert count_solutions(board, limit=2) == 1


def test_generate_no_given_cell_is_empty(rng: random.Random) -> None:
    board = generate_puzzle("easy", rng)
    for r in range(9):
        for c in range(9):
            if board.is_given(r, c):
                assert board.get(r, c) != 0


def test_generate_valid_row_constraints(rng: random.Random) -> None:
    board = generate_puzzle("easy", rng)
    assert _check_no_row_col_box_conflicts(board)


def test_generate_valid_col_constraints(rng: random.Random) -> None:
    board = generate_puzzle("medium", rng)
    assert _check_no_row_col_box_conflicts(board)


def test_generate_valid_box_constraints(rng: random.Random) -> None:
    board = generate_puzzle("hard", rng)
    assert _check_no_row_col_box_conflicts(board)


def test_generate_reproducible_with_seed() -> None:
    rng_a = random.Random(99)
    rng_b = random.Random(99)
    board_a = generate_puzzle("medium", rng_a)
    board_b = generate_puzzle("medium", rng_b)
    assert board_a.grid == board_b.grid
    assert board_a.givens == board_b.givens
