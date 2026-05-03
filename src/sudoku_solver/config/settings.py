DEFAULT_FPS: int = 60

# Speed is expressed in steps per second so it's intuitive to display.
# At 60 FPS, 5 steps/s means one step every 12 frames — clearly visible.
STEPS_PER_SECOND_MIN: int = 1
STEPS_PER_SECOND_MAX: int = 300
STEPS_PER_SECOND_DEFAULT: int = 5
STEPS_PER_SECOND_INCREMENT: int = 2

CLUES_BY_DIFFICULTY: dict[str, int] = {
    "easy": 47,
    "medium": 40,
    "hard": 31,
}
DEFAULT_DIFFICULTY: str = "medium"

BACKTRACK_HIGHLIGHT_FRAMES: int = 4
WINDOW_TITLE: str = "Sudoku Solver"
