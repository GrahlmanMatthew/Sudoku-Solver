from __future__ import annotations

import argparse
import logging
import os
import time
from collections.abc import Generator
from dataclasses import dataclass, field

import pygame

from sudoku_solver.board import Board
from sudoku_solver.config.constants import WINDOW_HEIGHT, WINDOW_WIDTH
from sudoku_solver.config.settings import (
    BACKTRACK_HIGHLIGHT_FRAMES,
    CLUES_BY_DIFFICULTY,
    DEFAULT_DIFFICULTY,
    DEFAULT_FPS,
    STEPS_PER_SECOND_DEFAULT,
    STEPS_PER_SECOND_INCREMENT,
    STEPS_PER_SECOND_MAX,
    STEPS_PER_SECOND_MIN,
    WINDOW_TITLE,
)
from sudoku_solver.generator import generate_puzzle
from sudoku_solver.renderer import Renderer, RenderStats
from sudoku_solver.solver import SolverStep, StepKind, solve

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

_DIFFICULTY_KEYS = {
    pygame.K_1: "easy",
    pygame.K_2: "medium",
    pygame.K_3: "hard",
}

# Accept both = and + (same physical key, with/without shift) plus numpad
_SPEED_UP_KEYS = {pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS}
_SPEED_DOWN_KEYS = {pygame.K_MINUS, pygame.K_KP_MINUS}


@dataclass
class AppState:
    """All mutable application state threaded through the game loop."""

    board: Board
    solver_gen: Generator[SolverStep, None, None]
    difficulty: str
    paused: bool = False
    solved: bool = False
    cells_placed: int = 0
    backtracks: int = 0
    start_time: float = field(default_factory=time.monotonic)
    steps_per_second: int = STEPS_PER_SECOND_DEFAULT
    _step_accumulator: float = 0.0
    highlight_cell: tuple[int, int] | None = None
    highlight_kind: StepKind | None = None
    highlight_frames_remaining: int = 0
    last_step: SolverStep | None = None


def main() -> None:
    """Parse CLI args, initialise Pygame, run the game loop."""
    args = _build_parser().parse_args()
    difficulty = args.difficulty

    logger.info("Starting %s (difficulty=%s)", WINDOW_TITLE, difficulty)

    pygame.init()
    surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    renderer = Renderer(surface)

    board, solver_gen = _new_session(difficulty)
    state = AppState(board=board, solver_gen=solver_gen, difficulty=difficulty)

    running = True
    while running:
        events = pygame.event.get()
        running = _handle_events(events, state)

        if state.highlight_frames_remaining > 0:
            state.highlight_frames_remaining -= 1
            if state.highlight_frames_remaining == 0:
                state.highlight_cell = None
                state.highlight_kind = None

        _advance_solver(state)

        stats = RenderStats(
            cells_placed=state.cells_placed,
            backtracks=state.backtracks,
            elapsed_seconds=time.monotonic() - state.start_time,
            difficulty=state.difficulty,
            steps_per_second=state.steps_per_second,
            paused=state.paused,
            solved=state.solved,
        )
        renderer.draw_frame(
            board=state.board,
            highlight_cell=state.highlight_cell,
            highlight_kind=state.highlight_kind,
            stats=stats,
        )
        pygame.display.flip()
        clock.tick(DEFAULT_FPS)

    pygame.quit()
    logger.info("Exiting.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=WINDOW_TITLE)
    parser.add_argument(
        "--difficulty",
        choices=list(CLUES_BY_DIFFICULTY.keys()),
        default=DEFAULT_DIFFICULTY,
        help="Starting difficulty (default: %(default)s)",
    )
    return parser


def _new_session(difficulty: str) -> tuple[Board, Generator[SolverStep, None, None]]:
    """Generate a fresh puzzle and return (board, solver_generator)."""
    logger.info("Generating %s puzzle…", difficulty)
    board = generate_puzzle(difficulty)
    return board, solve(board)


def _handle_events(events: list[pygame.event.Event], state: AppState) -> bool:
    """Process Pygame events; mutate state in place.

    Returns False when the user quits, True otherwise.
    """
    for event in events:
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            continue

        if event.key == pygame.K_ESCAPE:
            return False

        if event.key == pygame.K_SPACE:
            state.paused = not state.paused

        elif event.key == pygame.K_RIGHT and state.paused and not state.solved:
            _step_once(state)

        elif event.key in _SPEED_UP_KEYS:
            state.steps_per_second = min(
                state.steps_per_second + STEPS_PER_SECOND_INCREMENT, STEPS_PER_SECOND_MAX
            )

        elif event.key in _SPEED_DOWN_KEYS:
            state.steps_per_second = max(
                state.steps_per_second - STEPS_PER_SECOND_INCREMENT, STEPS_PER_SECOND_MIN
            )

        elif event.key == pygame.K_r:
            _reset_session(state, state.difficulty)

        elif event.key in _DIFFICULTY_KEYS:
            _reset_session(state, _DIFFICULTY_KEYS[event.key])

    return True


def _reset_session(state: AppState, difficulty: str) -> None:
    """Replace the current session with a fresh puzzle at the given difficulty."""
    board, solver_gen = _new_session(difficulty)
    state.board = board
    state.solver_gen = solver_gen
    state.difficulty = difficulty
    state.paused = False
    state.solved = False
    state.cells_placed = 0
    state.backtracks = 0
    state.start_time = time.monotonic()
    state._step_accumulator = 0.0
    state.highlight_cell = None
    state.highlight_kind = None
    state.highlight_frames_remaining = 0
    state.last_step = None


def _advance_solver(state: AppState) -> None:
    """Step the solver at the configured steps-per-second rate.

    Uses a fractional accumulator so fractional rates (e.g. 5 steps/s at 60 FPS)
    are distributed evenly across frames rather than bunching into one frame.
    Does nothing when paused, solved, or the generator is exhausted.
    """
    if state.paused or state.solved:
        return

    state._step_accumulator += state.steps_per_second / DEFAULT_FPS
    steps_this_frame = int(state._step_accumulator)
    state._step_accumulator -= steps_this_frame

    for _ in range(steps_this_frame):
        _step_once(state)
        if state.solved:
            break


def _step_once(state: AppState) -> None:
    """Advance the solver by exactly one step."""
    try:
        step = next(state.solver_gen)
    except StopIteration:
        state.solved = True
        return

    state.last_step = step

    if step.kind == StepKind.SOLVED:
        state.solved = True
        state.highlight_cell = None
        state.highlight_kind = None
        logger.info(
            "Solved! cells_placed=%d backtracks=%d",
            state.cells_placed,
            state.backtracks,
        )
        return

    if step.kind == StepKind.PLACE:
        state.cells_placed += 1
        state.board.set(step.row, step.col, step.digit)
    elif step.kind == StepKind.BACKTRACK:
        state.backtracks += 1
        state.board.set(step.row, step.col, 0)

    state.highlight_cell = (step.row, step.col)
    state.highlight_kind = step.kind
    state.highlight_frames_remaining = BACKTRACK_HIGHLIGHT_FRAMES
