from __future__ import annotations

from dataclasses import dataclass

import pygame

from sudoku_solver.board import Board
from sudoku_solver.config.constants import (
    BACKGROUND_COLOR,
    BACKTRACK_COLOR,
    CELL_SIZE,
    DIGIT_FONT_SIZE,
    GIVEN_BG_COLOR,
    GIVEN_DIGIT_COLOR,
    GRID_LINE_THICK_COLOR,
    GRID_LINE_THIN_COLOR,
    GRID_ORIGIN_X,
    GRID_ORIGIN_Y,
    GRID_SIZE,
    OVERLAY_BG_COLOR,
    OVERLAY_LINE_SPACING,
    OVERLAY_PADDING,
    OVERLAY_TEXT_COLOR,
    PLACED_COLOR,
    STATS_FONT_SIZE,
    THICK_LINE_WIDTH,
    THIN_LINE_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from sudoku_solver.solver import StepKind

_PANEL_TOP = GRID_ORIGIN_Y + GRID_SIZE + 16
_PANEL_HEIGHT = WINDOW_HEIGHT - _PANEL_TOP - 8
_PANEL_MID = WINDOW_WIDTH // 2

_CONTROLS: list[tuple[str, str]] = [
    ("SPACE", "Pause / Resume"),
    ("→", "Step (while paused)"),
    ("+ / -", "Speed up / down"),
    ("R", "New puzzle"),
    ("1 / 2 / 3", "Easy / Med / Hard"),
    ("ESC", "Quit"),
]


@dataclass
class RenderStats:
    """Live counters passed to the renderer each frame."""

    cells_placed: int
    backtracks: int
    elapsed_seconds: float
    difficulty: str
    steps_per_second: int
    paused: bool
    solved: bool


class Renderer:
    """Owns the Pygame display surface and renders every frame from scratch."""

    def __init__(self, surface: pygame.Surface) -> None:
        self._surface = surface
        self._digit_font = pygame.font.SysFont("monospace", DIGIT_FONT_SIZE, bold=True)
        self._stats_font = pygame.font.SysFont("monospace", STATS_FONT_SIZE)
        self._label_font = pygame.font.SysFont("monospace", STATS_FONT_SIZE - 2)

    def draw_frame(
        self,
        board: Board,
        highlight_cell: tuple[int, int] | None,
        highlight_kind: StepKind | None,
        stats: RenderStats,
    ) -> None:
        """Clear the surface and draw a complete frame."""
        self._draw_background()
        self._draw_cells(board, highlight_cell, highlight_kind)
        self._draw_grid_lines()
        self._draw_bottom_panel(stats)

    def _draw_background(self) -> None:
        self._surface.fill(BACKGROUND_COLOR)

    def _draw_grid_lines(self) -> None:
        for i in range(10):
            is_box_border = i % 3 == 0
            color = GRID_LINE_THICK_COLOR if is_box_border else GRID_LINE_THIN_COLOR
            width = THICK_LINE_WIDTH if is_box_border else THIN_LINE_WIDTH
            x = GRID_ORIGIN_X + i * CELL_SIZE
            y = GRID_ORIGIN_Y + i * CELL_SIZE
            pygame.draw.line(
                self._surface,
                color,
                (x, GRID_ORIGIN_Y),
                (x, GRID_ORIGIN_Y + GRID_SIZE),
                width,
            )
            pygame.draw.line(
                self._surface,
                color,
                (GRID_ORIGIN_X, y),
                (GRID_ORIGIN_X + GRID_SIZE, y),
                width,
            )

    def _draw_cells(
        self,
        board: Board,
        highlight_cell: tuple[int, int] | None,
        highlight_kind: StepKind | None,
    ) -> None:
        for r in range(9):
            for c in range(9):
                rect = self._cell_rect(r, c)
                digit = board.get(r, c)

                if (r, c) == highlight_cell and highlight_kind is not None:
                    bg = PLACED_COLOR if highlight_kind == StepKind.PLACE else BACKTRACK_COLOR
                    _draw_rect_alpha(self._surface, (*bg, 80), rect)
                elif board.is_given(r, c):
                    _draw_rect_alpha(self._surface, (*GIVEN_BG_COLOR, 255), rect)

                if digit != 0:
                    if board.is_given(r, c):
                        color = GIVEN_DIGIT_COLOR
                    elif (r, c) == highlight_cell and highlight_kind == StepKind.PLACE:
                        color = PLACED_COLOR
                    elif (r, c) == highlight_cell and highlight_kind == StepKind.BACKTRACK:
                        color = BACKTRACK_COLOR
                    else:
                        color = PLACED_COLOR
                    self._draw_digit(r, c, digit, color)

    def _draw_digit(self, row: int, col: int, digit: int, color: tuple[int, int, int]) -> None:
        rect = self._cell_rect(row, col)
        text = self._digit_font.render(str(digit), True, color)
        text_rect = text.get_rect(center=rect.center)
        self._surface.blit(text, text_rect)

    def _draw_bottom_panel(self, stats: RenderStats) -> None:
        # Draw semi-transparent panel background
        panel = pygame.Surface((WINDOW_WIDTH - GRID_ORIGIN_X * 2, _PANEL_HEIGHT), pygame.SRCALPHA)
        panel.fill(OVERLAY_BG_COLOR)
        self._surface.blit(panel, (GRID_ORIGIN_X, _PANEL_TOP))

        self._draw_stats_column(stats)
        self._draw_controls_column()

        # Divider
        mid_x = GRID_ORIGIN_X + (WINDOW_WIDTH - GRID_ORIGIN_X * 2) // 2
        pygame.draw.line(
            self._surface,
            (60, 60, 70),
            (mid_x, _PANEL_TOP + 8),
            (mid_x, _PANEL_TOP + _PANEL_HEIGHT - 8),
            1,
        )

    def _draw_stats_column(self, stats: RenderStats) -> None:
        x = GRID_ORIGIN_X + OVERLAY_PADDING
        y = _PANEL_TOP + OVERLAY_PADDING

        status = "SOLVED!" if stats.solved else ("PAUSED" if stats.paused else "Solving…")
        status_color = (
            (120, 220, 120) if stats.solved else (220, 180, 60) if stats.paused else (160, 160, 160)
        )

        rows = [
            (f"Difficulty:  {stats.difficulty.capitalize()}", OVERLAY_TEXT_COLOR),
            (f"Speed:       {stats.steps_per_second} steps/s", OVERLAY_TEXT_COLOR),
            (f"Placed:      {stats.cells_placed}", OVERLAY_TEXT_COLOR),
            (f"Backtracks:  {stats.backtracks}", OVERLAY_TEXT_COLOR),
            (f"Time:        {stats.elapsed_seconds:.1f}s", OVERLAY_TEXT_COLOR),
            (status, status_color),
        ]

        for text, color in rows:
            surf = self._stats_font.render(text, True, color)
            self._surface.blit(surf, (x, y))
            y += OVERLAY_LINE_SPACING

    def _draw_controls_column(self) -> None:
        mid_x = GRID_ORIGIN_X + (WINDOW_WIDTH - GRID_ORIGIN_X * 2) // 2
        x = mid_x + OVERLAY_PADDING
        y = _PANEL_TOP + OVERLAY_PADDING

        key_color = (180, 180, 200)
        desc_color = (110, 110, 120)

        for key, desc in _CONTROLS:
            key_surf = self._label_font.render(f"{key:<10}", True, key_color)
            desc_surf = self._label_font.render(desc, True, desc_color)
            self._surface.blit(key_surf, (x, y))
            self._surface.blit(desc_surf, (x + 80, y))
            y += OVERLAY_LINE_SPACING - 2

    def _cell_rect(self, row: int, col: int) -> pygame.Rect:
        return pygame.Rect(
            GRID_ORIGIN_X + col * CELL_SIZE,
            GRID_ORIGIN_Y + row * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )


def _draw_rect_alpha(
    surface: pygame.Surface,
    color: tuple[int, int, int, int],
    rect: pygame.Rect,
) -> None:
    layer = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    layer.fill(color)
    surface.blit(layer, rect.topleft)
