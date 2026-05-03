from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum, auto

from sudoku_solver.board import Board, find_empty_cell, is_valid_placement


class StepKind(Enum):
    PLACE = auto()
    BACKTRACK = auto()
    SOLVED = auto()


@dataclass
class SolverStep:
    """Single unit of solver progress yielded by the generator."""

    kind: StepKind
    row: int
    col: int
    digit: int
    board_snapshot: Board


def solve(board: Board) -> Generator[SolverStep, None, None]:
    """Backtracking solver generator.

    Yields one SolverStep per placement or backtrack, then a final SOLVED step.
    Mutates board in-place; each step's board_snapshot is an independent copy.
    Raises StopIteration without a SOLVED step if the puzzle is unsolvable.
    """
    yield from _solve_recursive(board)


def _solve_recursive(board: Board) -> Generator[SolverStep, None, bool]:
    cell = find_empty_cell(board)
    if cell is None:
        yield SolverStep(
            kind=StepKind.SOLVED,
            row=-1,
            col=-1,
            digit=0,
            board_snapshot=board.copy(),
        )
        return True

    row, col = cell
    for digit in range(1, 10):
        if is_valid_placement(board, row, col, digit):
            board.set(row, col, digit)
            yield SolverStep(
                kind=StepKind.PLACE,
                row=row,
                col=col,
                digit=digit,
                board_snapshot=board.copy(),
            )
            solved = yield from _solve_recursive(board)
            if solved:
                return True
            board.set(row, col, 0)
            yield SolverStep(
                kind=StepKind.BACKTRACK,
                row=row,
                col=col,
                digit=0,
                board_snapshot=board.copy(),
            )

    return False


def count_solutions(board: Board, limit: int = 2) -> int:
    """Count solutions up to limit using backtracking with early exit.

    Returns 0 (unsolvable), 1 (unique), or up to limit (multiple solutions).
    """
    found = [0]
    _count_recursive(board.copy(), found, limit)
    return found[0]


def _count_recursive(board: Board, found: list[int], limit: int) -> None:
    if found[0] >= limit:
        return
    cell = find_empty_cell(board)
    if cell is None:
        found[0] += 1
        return
    row, col = cell
    for digit in range(1, 10):
        if is_valid_placement(board, row, col, digit):
            board.set(row, col, digit)
            _count_recursive(board, found, limit)
            board.set(row, col, 0)
            if found[0] >= limit:
                return
