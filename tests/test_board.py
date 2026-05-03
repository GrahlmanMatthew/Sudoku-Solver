from sudoku_solver.board import Board, find_empty_cell, is_valid_placement


def test_empty_board_all_zeros() -> None:
    board = Board.empty()
    assert all(board.get(r, c) == 0 for r in range(9) for c in range(9))


def test_set_and_get_roundtrip() -> None:
    board = Board.empty()
    board.set(4, 7, 5)
    assert board.get(4, 7) == 5


def test_is_given_mask() -> None:
    grid = [[0] * 9 for _ in range(9)]
    givens = [[False] * 9 for _ in range(9)]
    givens[0][0] = True
    board = Board.from_grid(grid, givens)
    assert board.is_given(0, 0)
    assert not board.is_given(0, 1)


def test_copy_is_independent() -> None:
    board = Board.empty()
    board.set(0, 0, 3)
    clone = board.copy()
    clone.set(0, 0, 9)
    assert board.get(0, 0) == 3


def test_is_full_false_when_cells_remain() -> None:
    board = Board.empty()
    assert not board.is_full()


def test_is_full_true_when_all_filled() -> None:
    board = Board.empty()
    for r in range(9):
        for c in range(9):
            board.set(r, c, 1)
    assert board.is_full()


def test_is_valid_placement_row_conflict() -> None:
    board = Board.empty()
    board.set(0, 3, 7)
    assert not is_valid_placement(board, 0, 8, 7)


def test_is_valid_placement_col_conflict() -> None:
    board = Board.empty()
    board.set(5, 2, 4)
    assert not is_valid_placement(board, 1, 2, 4)


def test_is_valid_placement_box_conflict() -> None:
    board = Board.empty()
    board.set(0, 0, 2)
    assert not is_valid_placement(board, 2, 2, 2)


def test_is_valid_placement_accepts_valid_digit() -> None:
    board = Board.empty()
    board.set(0, 0, 1)
    assert is_valid_placement(board, 1, 1, 2)


def test_find_empty_cell_returns_none_when_full() -> None:
    board = Board.empty()
    for r in range(9):
        for c in range(9):
            board.set(r, c, 1)
    assert find_empty_cell(board) is None


def test_find_empty_cell_returns_first_empty_reading_order() -> None:
    board = Board.empty()
    board.set(0, 0, 1)
    board.set(0, 1, 2)
    assert find_empty_cell(board) == (0, 2)
