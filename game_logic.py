"""
game_logic.py - Game settings and session-state rules for Snake Arena.

This file contains NO user-interface code. It decides:
  * the game settings (board size, points per food, difficulty speeds)
  * what each button does to the game state (start, pause/resume, restart)
  * how messages ("events") coming back from the game board update the
    score, the high score and the game status.

Every function takes a dictionary-like `state` object. In the real app this
is `st.session_state`; in the tests it is a plain Python dict. Keeping
Streamlit out of this file makes the rules easy to read and easy to test.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Game settings (the browser board receives these values from Python, so they
# are defined in exactly one place).
# ---------------------------------------------------------------------------
BOARD_SIZE = 20          # The board is BOARD_SIZE x BOARD_SIZE cells.
INITIAL_LENGTH = 3       # Number of cells the snake starts with.
POINTS_PER_FOOD = 10     # Score added each time the snake eats.

# Possible game statuses.
READY = "ready"          # Waiting for the player to press Start.
RUNNING = "running"      # Snake is moving.
PAUSED = "paused"        # Game frozen; can be resumed.
GAME_OVER = "over"       # Snake hit a wall or itself.
WON = "won"              # Snake filled the entire board (very rare!).

STATUS_LABELS = {
    READY: "Ready",
    RUNNING: "Playing",
    PAUSED: "Paused",
    GAME_OVER: "Game Over",
    WON: "You Win!",
}


@dataclass(frozen=True)
class Difficulty:
    """One difficulty level. `tick_ms` is the time between two snake moves."""

    name: str
    tick_ms: int

    @property
    def moves_per_second(self) -> float:
        return round(1000 / self.tick_ms, 1)


# Smaller tick_ms = the snake moves more often = faster game.
DIFFICULTIES = {
    "Easy": Difficulty("Easy", 180),
    "Medium": Difficulty("Medium", 120),
    "Hard": Difficulty("Hard", 75),
}
DEFAULT_DIFFICULTY = "Medium"


def get_difficulty(name: str) -> Difficulty:
    """Return the Difficulty for `name`, falling back to the default level."""
    return DIFFICULTIES.get(name, DIFFICULTIES[DEFAULT_DIFFICULTY])


def max_possible_score(board_size: int = BOARD_SIZE,
                       initial_length: int = INITIAL_LENGTH) -> int:
    """Highest score possible: the snake fills every cell of the board."""
    return (board_size * board_size - initial_length) * POINTS_PER_FOOD


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state(state) -> None:
    """Create every key the app needs, but only if it doesn't exist yet.

    Streamlit re-runs app.py from top to bottom after every click. Because we
    only set *missing* keys, the score and high score survive those re-runs.
    """
    defaults = {
        "status": READY,
        "score": 0,
        "high_score": 0,
        "games_played": 0,
        "difficulty": DEFAULT_DIFFICULTY,
        "command": None,        # Last command sent to the board ("start", ...)
        "command_id": 0,        # Increases with every command (see send_command)
        "game_id": 0,           # Identifies the current game
        "last_event_id": None,  # Last board event we already processed
        "best_before_game": 0,  # High score when the current game started
        "new_record": False,    # True if the last finished game beat the record
    }
    for key, value in defaults.items():
        if key not in state:
            state[key] = value


def send_command(state, command: str) -> None:
    """Queue a command for the game board.

    The board can't be "called" like a function - it only receives the latest
    values every time the app re-runs. A counter (command_id) lets the board
    notice that a command is NEW, even if the same command is sent twice.
    """
    state["command"] = command
    state["command_id"] += 1


def start_game(state) -> None:
    """Start a brand-new game (used by both Start and Restart buttons)."""
    state["score"] = 0
    state["status"] = RUNNING
    state["new_record"] = False
    state["best_before_game"] = state["high_score"]
    send_command(state, "start")
    # The new game is identified by the command that started it. Events from
    # an older game (that arrive late) are ignored by apply_board_event().
    state["game_id"] = state["command_id"]


def toggle_pause(state) -> None:
    """Pause a running game, or resume a paused one. Otherwise do nothing."""
    if state["status"] == RUNNING:
        state["status"] = PAUSED
        send_command(state, "pause")
    elif state["status"] == PAUSED:
        state["status"] = RUNNING
        send_command(state, "resume")


def is_valid_score(value) -> bool:
    """Check that a score from the browser is believable.

    It must be a whole number, a multiple of POINTS_PER_FOOD, and not larger
    than the maximum possible score. (bool is excluded because True == 1.)
    """
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= max_possible_score()
        and value % POINTS_PER_FOOD == 0
    )


def apply_board_event(state, event) -> bool:
    """Update the session state from an event sent by the game board.

    An event is a small dict such as:
        {"id": "k3x-7", "type": "score", "score": 30, "game_id": 4}

    Event types:
        ready  - the board was (re)loaded and is waiting for Start
        score  - the snake ate food
        pause  - the player pressed Space to pause
        resume - the player pressed Space to resume
        over   - the snake crashed
        won    - the snake filled the board

    Returns True if the state changed, False if the event was ignored.
    """
    if not isinstance(event, dict):
        return False

    # Streamlit keeps returning the board's LAST value on every re-run, so we
    # remember which event we already handled and skip it the second time.
    event_id = event.get("id")
    if event_id is None or event_id == state["last_event_id"]:
        return False
    state["last_event_id"] = event_id

    event_type = event.get("type")

    # A freshly loaded board has no game running, so reset to "ready".
    if event_type == "ready":
        if state["status"] in (RUNNING, PAUSED):
            state["status"] = READY
            state["score"] = 0
        return True

    # Ignore late events that belong to an older game (e.g. the player hit
    # Restart a split second after eating food).
    if event.get("game_id") != state["game_id"]:
        return False

    score = event.get("score")
    if not is_valid_score(score):
        return False

    state["score"] = score
    state["high_score"] = max(state["high_score"], score)

    if event_type == "pause" and state["status"] == RUNNING:
        state["status"] = PAUSED
    elif event_type == "resume" and state["status"] == PAUSED:
        state["status"] = RUNNING
    elif event_type in ("over", "won") and state["status"] in (RUNNING, PAUSED):
        state["status"] = GAME_OVER if event_type == "over" else WON
        state["games_played"] += 1
        state["new_record"] = score > state["best_before_game"]
    return True
