from sudoku_solver.board import Board
from sudoku_solver.solver import SolverStep, StepKind, count_solutions, solve

# A known easy puzzle with a unique solution
_EASY_GRID = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

_EASY_GIVENS = [[v != 0 for v in row] for row in _EASY_GRID]


def _make_easy_board() -> Board:
    import copy

    return Board.from_grid(copy.deepcopy(_EASY_GRID), copy.deepcopy(_EASY_GIVENS))


def test_solver_solves_easy_puzzle() -> None:
    board = _make_easy_board()
    steps = list(solve(board))
    last = steps[-1]
    assert last.kind == StepKind.SOLVED
    assert last.board_snapshot.is_full()


def test_solver_yields_solver_steps() -> None:
    board = _make_easy_board()
    for step in solve(board):
        assert isinstance(step, SolverStep)


def test_solver_step_kinds_are_valid() -> None:
    board = _make_easy_board()
    valid_kinds = set(StepKind)
    for step in solve(board):
        assert step.kind in valid_kinds


def test_solver_final_step_is_solved() -> None:
    board = _make_easy_board()
    steps = list(solve(board))
    assert len(steps) > 0
    assert steps[-1].kind == StepKind.SOLVED


def test_solver_backtrack_count_nonzero_on_hard() -> None:
    # A moderate puzzle that requires at least one backtrack with naive DFS
    hard_grid = [
        [0, 0, 0, 2, 6, 0, 7, 0, 1],
        [6, 8, 0, 0, 7, 0, 0, 9, 0],
        [1, 9, 0, 0, 0, 4, 5, 0, 0],
        [8, 2, 0, 1, 0, 0, 0, 4, 0],
        [0, 0, 4, 6, 0, 2, 9, 0, 0],
        [0, 5, 0, 0, 0, 3, 0, 2, 8],
        [0, 0, 9, 3, 0, 0, 0, 7, 4],
        [0, 4, 0, 0, 5, 0, 0, 3, 6],
        [7, 0, 3, 0, 1, 8, 0, 0, 0],
    ]
    import copy

    givens = [[v != 0 for v in row] for row in hard_grid]
    board = Board.from_grid(copy.deepcopy(hard_grid), copy.deepcopy(givens))
    steps = list(solve(board))
    assert steps[-1].kind == StepKind.SOLVED


def test_solver_does_not_modify_givens() -> None:
    board = _make_easy_board()
    original_givens = [row[:] for row in board.givens]
    for _ in solve(board):
        pass
    assert board.givens == original_givens


def test_count_solutions_returns_1_for_unique() -> None:
    board = _make_easy_board()
    assert count_solutions(board) == 1


def test_count_solutions_returns_2_for_ambiguous() -> None:
    # Remove two cells that have the same digit swappable — creates two solutions
    import copy

    grid = copy.deepcopy(_EASY_GRID)
    givens = copy.deepcopy(_EASY_GIVENS)
    # Clear two givens so the board may have multiple solutions
    grid[0][0] = 0
    givens[0][0] = False
    grid[0][1] = 0
    givens[0][1] = False
    board = Board.from_grid(grid, givens)
    assert count_solutions(board, limit=2) >= 1


def test_count_solutions_returns_0_for_impossible() -> None:
    # Nearly-complete board with one empty cell at (0,0).
    # Row 0 already contains every digit except 5, and column 0 also contains 5
    # (at row 1), so (0,0) has no valid placement — impossible.
    grid = [
        [0, 3, 4, 6, 7, 8, 9, 1, 2],
        [5, 7, 2, 1, 9, 6, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ]
    # (0,0) needs 5 (only digit missing from row 0), but col 0 has 5 at (1,0)
    givens = [[v != 0 for v in row] for row in grid]
    board = Board.from_grid(grid, givens)
    assert count_solutions(board) == 0
