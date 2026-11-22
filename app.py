"""
app.py - Snake Arena (the Streamlit user interface).

Run locally with:
    streamlit run app.py

How the pieces fit together:
  * app.py         - page layout, score cards, buttons, instructions (this file)
  * game_logic.py  - settings and rules for the session state (no UI code)
  * frontend/      - the game board that runs in the browser (HTML + JS)
  * assets/style.css - the arcade look of the page
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import game_logic as gl

BASE_DIR = Path(__file__).parent
CSS_FILE = BASE_DIR / "assets" / "style.css"
FRONTEND_DIR = BASE_DIR / "frontend"
BOARD_KEY = "snake_board"

# set_page_config must be the first Streamlit command in the script.
st.set_page_config(
    page_title="Snake Arena by Jayanth Reddy",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Register the game board as a Streamlit "custom component". Streamlit serves
# the files in frontend/ and shows frontend/index.html inside the page.
snake_board = components.declare_component("snake_board", path=str(FRONTEND_DIR))


def load_css(path: Path) -> None:
    """Add our stylesheet to the page. The game still works without it."""
    try:
        css = path.read_text(encoding="utf-8")
    except OSError:
        st.warning(f"Could not load the stylesheet at {path}. Using default styles.")
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def stat_card(label: str, value, accent: str = "") -> str:
    """HTML for one score card. `accent` picks an extra CSS colour class."""
    return (
        f'<div class="stat-card {accent}">'
        f'<span class="stat-label">{label}</span>'
        f'<span class="stat-value">{value}</span>'
        f"</div>"
    )


def render_stats(placeholder) -> None:
    """Fill the row of cards: score, high score, speed and status."""
    state = st.session_state
    difficulty = gl.get_difficulty(state.difficulty)
    status_class = {
        gl.RUNNING: "accent-green",
        gl.PAUSED: "accent-amber",
        gl.GAME_OVER: "accent-red",
        gl.WON: "accent-green",
    }.get(state.status, "")
    cards = [
        stat_card("Score", state.score, "accent-green"),
        stat_card("High Score", state.high_score, "accent-amber"),
        stat_card("Game Speed", f"{difficulty.name} · {difficulty.moves_per_second}/s"),
        stat_card("Status", gl.STATUS_LABELS[state.status], status_class),
    ]
    placeholder.markdown(
        f'<div class="stat-grid">{"".join(cards)}</div>', unsafe_allow_html=True
    )


def render_controls() -> None:
    """Difficulty selector, the game buttons and the instructions."""
    state = st.session_state
    playing = state.status in (gl.RUNNING, gl.PAUSED)

    st.markdown('<div class="panel-title">Difficulty</div>', unsafe_allow_html=True)
    # The radio is linked to st.session_state["difficulty"] through its key.
    # It is locked during a game so the speed can't change mid-game.
    st.radio(
        "Difficulty",
        options=list(gl.DIFFICULTIES),
        key="difficulty",
        horizontal=True,
        disabled=playing,
        label_visibility="collapsed",
        help="Easy is slow, Medium is normal, Hard is fast. "
             "You can change it when no game is running.",
    )

    st.markdown('<div class="panel-title">Controls</div>', unsafe_allow_html=True)
    # on_click callbacks run BEFORE the script re-runs, so the new command is
    # already in session_state when the board is drawn again.
    st.button(
        "▶  Start Game",
        on_click=gl.start_game,
        args=(state,),
        disabled=playing,
        type="primary",
        width="stretch",
    )
    pause_label = "▶  Resume" if state.status == gl.PAUSED else "⏸  Pause"
    st.button(
        pause_label,
        on_click=gl.toggle_pause,
        args=(state,),
        disabled=not playing,
        width="stretch",
    )
    st.button(
        "↻  Restart Game",
        on_click=gl.start_game,
        args=(state,),
        disabled=state.status == gl.READY,
        width="stretch",
    )

    st.markdown(
        """
        <div class="how-to">
          <div class="panel-title">How to play</div>
          <ul>
            <li>Press <b>Start Game</b>, then steer with
                <kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd> or
                <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd>.</li>
            <li>On a phone or tablet, <b>swipe</b> on the board.</li>
            <li>Eat the <span class="food-dot"></span> food to grow and earn
                <b>10 points</b>.</li>
            <li>Don't hit the walls or your own tail.</li>
            <li><kbd>Space</kbd> or the Pause button pauses the game.</li>
            <li>If the keys don't respond, click once on the board.</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    gl.init_state(st.session_state)
    load_css(CSS_FILE)

    # ----- Header ---------------------------------------------------------
    st.markdown(
        """
        <div class="hero">
          <h1 class="hero-title">SNAKE ARENA</h1>
          <h3 class="hero-title">BY JAYANTH REDDY</h3>
          <p class="hero-subtitle">Classic Snake Game</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # The cards are drawn at the END of the script (into this placeholder) so
    # they show the latest score reported by the board below.
    stats_placeholder = st.empty()

    board_col, side_col = st.columns([3, 2], gap="large")

    # ----- Game board -------------------------------------------------------
    with board_col:
        difficulty = gl.get_difficulty(st.session_state.difficulty)
        state = st.session_state
        # Values sent to the board. The board returns its latest event (or
        # None). The fixed `key` keeps the same board alive across re-runs.
        event = snake_board(
            board_size=gl.BOARD_SIZE,
            initial_length=gl.INITIAL_LENGTH,
            points_per_food=gl.POINTS_PER_FOOD,
            tick_ms=difficulty.tick_ms,
            high_score=state.high_score,
            command=state.command,
            command_id=state.command_id,
            game_id=state.game_id,
            key=BOARD_KEY,
            default=None,
        )
        finished_before = state.status in (gl.GAME_OVER, gl.WON)
        gl.apply_board_event(state, event)
        just_finished = not finished_before and state.status in (gl.GAME_OVER, gl.WON)

    if just_finished and st.session_state.new_record:
        st.toast(f"New high score: {st.session_state.high_score}!", icon="🏆")

    # ----- Side panel -------------------------------------------------------
    with side_col:
        render_controls()

    render_stats(stats_placeholder)

    st.markdown(
        '<div class="footer">Built with Python &amp; Streamlit · '
        f"Games played this session: {st.session_state.games_played}</div>",
        unsafe_allow_html=True,
    )


main()
