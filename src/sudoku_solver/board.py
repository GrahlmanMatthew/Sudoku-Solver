from __future__ import annotations

import copy
from dataclasses import dataclass


@dataclass
class Board:
    """9×9 grid plus a boolean mask marking given (clue) cells."""

    grid: list[list[int]]
    givens: list[list[bool]]

    @classmethod
    def empty(cls) -> Board:
        """Return a fully empty 9×9 board with no givens."""
        return cls(
            grid=[[0] * 9 for _ in range(9)],
            givens=[[False] * 9 for _ in range(9)],
        )

    @classmethod
    def from_grid(cls, grid: list[list[int]], givens: list[list[bool]]) -> Board:
        """Construct a Board from existing grid and givens mask."""
        return cls(grid=grid, givens=givens)

    def copy(self) -> Board:
        """Return a deep copy of this board."""
        return Board(
            grid=copy.deepcopy(self.grid),
            givens=copy.deepcopy(self.givens),
        )

    def get(self, row: int, col: int) -> int:
        """Return the digit at (row, col); 0 means empty."""
        return self.grid[row][col]

    def set(self, row: int, col: int, value: int) -> None:
        """Place a digit (1–9) or clear (0) at (row, col)."""
        self.grid[row][col] = value

    def is_given(self, row: int, col: int) -> bool:
        """Return True if (row, col) is a given clue cell."""
        return self.givens[row][col]

    def is_empty(self, row: int, col: int) -> bool:
        """Return True if (row, col) holds no digit."""
        return self.grid[row][col] == 0

    def is_full(self) -> bool:
        """Return True when every cell is filled."""
        return all(self.grid[r][c] != 0 for r in range(9) for c in range(9))


def is_valid_placement(board: Board, row: int, col: int, digit: int) -> bool:
    """Return True if placing digit at (row, col) violates no row/col/box constraint."""
    if digit in board.grid[row]:
        return False
    if digit in (board.grid[r][col] for r in range(9)):
        return False
    box_row, box_col = (row // 3) * 3, (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board.grid[r][c] == digit:
                return False
    return True


def find_empty_cell(board: Board) -> tuple[int, int] | None:
    """Return (row, col) of the first empty cell in reading order, or None if full."""
    for r in range(9):
        for c in range(9):
            if board.grid[r][c] == 0:
                return (r, c)
    return None
