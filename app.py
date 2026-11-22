
"""
app.py - Snake Arena (Streamlit user interface)

Run locally with:
    streamlit run app.py

Project structure:
    app.py         - page layout, score cards, controls and embedded CSS
    game_logic.py  - game settings and rules
    frontend/      - HTML + JavaScript game board
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import game_logic as gl


BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"
BOARD_KEY = "snake_board"


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Snake Arena by Jayanth Reddy",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------
# Register custom frontend component
# ---------------------------------------------------------------------

snake_board = components.declare_component(
    "snake_board",
    path=str(FRONTEND_DIR),
)


# ---------------------------------------------------------------------
# Embedded CSS
# ---------------------------------------------------------------------

def load_css() -> None:
    """Load custom arcade CSS directly into the Streamlit app."""

    css = """
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Inter:wght@400;600;700&display=swap');

    :root {
        --bg: #0b0f1a;
        --bg-glow: #10203a;
        --card: #111827;
        --card-border: #1f2b45;
        --neon: #39ff14;
        --amber: #ffb020;
        --red: #ff5a36;
        --text: #e6edf3;
        --muted: #8b98b0;
        --radius: 16px;
    }

    /* ---------- Page background and fonts ---------- */

    .stApp {
        background:
            radial-gradient(
                900px 500px at 15% -10%,
                rgba(57, 255, 20, 0.08),
                transparent 60%
            ),
            radial-gradient(
                800px 500px at 100% 0%,
                rgba(32, 120, 255, 0.10),
                transparent 60%
            ),
            var(--bg);

        color: var(--text);
        font-family: "Inter", "Segoe UI", system-ui, sans-serif;
    }

    /* Hide default Streamlit decorations */

    #MainMenu,
    footer,
    [data-testid="stDecoration"] {
        display: none !important;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1150px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* ---------- Header ---------- */

    .hero {
        text-align: center;
        margin-bottom: 1.2rem;
    }

    .hero-title {
        margin: 0;
        padding: 0;

        font-family: "Orbitron", "Segoe UI", sans-serif !important;
        font-weight: 800;
        font-size: clamp(2.2rem, 7vw, 3.6rem);
        letter-spacing: 0.14em;

        color: var(--neon) !important;

        text-shadow:
            0 0 12px rgba(57, 255, 20, 0.6),
            0 0 40px rgba(57, 255, 20, 0.25);
    }

    .hero-subtitle {
        margin: 0.2rem 0 0;
        color: var(--muted);
        font-size: 1rem;
        letter-spacing: 0.3em;
        text-transform: uppercase;
    }

    /* ---------- Score cards ---------- */

    .stat-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 1.4rem;
    }

    .stat-card {
        display: flex;
        flex-direction: column;
        gap: 4px;

        padding: 14px 18px;
        border-radius: var(--radius);

        background: linear-gradient(180deg, #141d30, var(--card));
        border: 1px solid var(--card-border);

        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }

    .stat-label {
        color: var(--muted);
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .stat-value {
        font-family: "Orbitron", "Segoe UI", sans-serif;
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--text);

        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .accent-green .stat-value {
        color: var(--neon);
        text-shadow: 0 0 10px rgba(57, 255, 20, 0.4);
    }

    .accent-amber .stat-value {
        color: var(--amber);
    }

    .accent-red .stat-value {
        color: var(--red);
    }

    /* ---------- Side panel ---------- */

    .panel-title {
        margin: 0.4rem 0 0.5rem;

        color: var(--muted);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    /* Difficulty radio buttons */

    div[data-testid="stRadio"] [role="radiogroup"] {
        gap: 8px;
        flex-wrap: wrap;
    }

    div[data-testid="stRadio"] [role="radiogroup"] > label {
        margin: 0;
        padding: 6px 16px;

        border-radius: 999px;
        background: var(--card);
        border: 1px solid var(--card-border);

        transition: border-color 0.15s ease;
    }

    div[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {
        border-color: var(--neon);
        box-shadow: 0 0 12px rgba(57, 255, 20, 0.25);
    }

    /* ---------- Buttons ---------- */

    .stButton > button {
        min-height: 48px;
        border-radius: 12px;

        font-weight: 700;
        letter-spacing: 0.04em;

        background: var(--card);
        border: 1px solid var(--card-border);
        color: var(--text);

        transition:
            transform 0.08s ease,
            border-color 0.15s ease,
            box-shadow 0.15s ease;
    }

    .stButton > button:hover:not(:disabled) {
        border-color: var(--neon);
        color: var(--neon);
        box-shadow: 0 0 14px rgba(57, 255, 20, 0.25);
    }

    .stButton > button:active:not(:disabled) {
        transform: translateY(1px);
    }

    .stButton > button[kind="primary"] {
        background: var(--neon);
        border-color: var(--neon);
        color: #06210a;
        box-shadow: 0 0 18px rgba(57, 255, 20, 0.35);
    }

    .stButton > button[kind="primary"]:hover:not(:disabled) {
        color: #06210a;
        filter: brightness(1.08);
    }

    .stButton > button:disabled {
        opacity: 0.4;
    }

    /* ---------- Instructions card ---------- */

    .how-to {
        margin-top: 1rem;
        padding: 14px 18px;

        border-radius: var(--radius);
        background: var(--card);
        border: 1px solid var(--card-border);
    }

    .how-to ul {
        margin: 0;
        padding-left: 1.1rem;
        color: var(--text);
    }

    .how-to li {
        margin: 0.35rem 0;
        font-size: 0.92rem;
        line-height: 1.5;
    }

    .how-to kbd {
        display: inline-block;
        min-width: 22px;

        margin: 0 2px;
        padding: 0 6px;

        border: 1px solid var(--card-border);
        border-bottom-width: 2px;
        border-radius: 6px;

        background: #0d1424;
        color: var(--text);

        font-size: 0.78rem;
        text-align: center;
    }

    .food-dot {
        display: inline-block;
        width: 10px;
        height: 10px;

        border-radius: 50%;
        background: var(--red);
        box-shadow: 0 0 8px var(--red);
    }

    /* ---------- Board and footer ---------- */

    iframe {
        border: none;
    }

    .footer {
        margin-top: 2rem;
        text-align: center;
        color: var(--muted);
        font-size: 0.8rem;
    }

    /* ---------- Responsive layout ---------- */

    @media (max-width: 760px) {
        .stat-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
        }

        .stat-card {
            padding: 12px 14px;
        }

        .stat-value {
            font-size: 1.1rem;
        }

        .hero-subtitle {
            letter-spacing: 0.18em;
        }
    }
    """

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Score cards
# ---------------------------------------------------------------------

def stat_card(label: str, value, accent: str = "") -> str:
    """Generate HTML for a score card."""

    return (
        f'<div class="stat-card {accent}">'
        f'<span class="stat-label">{label}</span>'
        f'<span class="stat-value">{value}</span>'
        f"</div>"
    )


def render_stats(placeholder) -> None:
    """Render score, high score, game speed and status cards."""

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
        stat_card(
            "Game Speed",
            f"{difficulty.name} · {difficulty.moves_per_second}/s",
        ),
        stat_card(
            "Status",
            gl.STATUS_LABELS[state.status],
            status_class,
        ),
    ]

    placeholder.markdown(
        f'<div class="stat-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Game controls
# ---------------------------------------------------------------------

def render_controls() -> None:
    """Render difficulty selector, game buttons and instructions."""

    state = st.session_state
    playing = state.status in (gl.RUNNING, gl.PAUSED)

    # Difficulty

    st.markdown(
        '<div class="panel-title">Difficulty</div>',
        unsafe_allow_html=True,
    )

    st.radio(
        "Difficulty",
        options=list(gl.DIFFICULTIES),
        key="difficulty",
        horizontal=True,
        disabled=playing,
        label_visibility="collapsed",
        help=(
            "Easy is slow, Medium is normal, Hard is fast. "
            "You can change it when no game is running."
        ),
    )

    # Controls

    st.markdown(
        '<div class="panel-title">Controls</div>',
        unsafe_allow_html=True,
    )

    st.button(
        "▶  Start Game",
        on_click=gl.start_game,
        args=(state,),
        disabled=playing,
        type="primary",
        width="stretch",
    )

    pause_label = (
        "▶  Resume"
        if state.status == gl.PAUSED
        else "⏸  Pause"
    )

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

    # Instructions

    st.markdown(
        """
        <div class="how-to">
            <div class="panel-title">How to play</div>
            <ul>
                <li>
                    Press <b>Start Game</b>, then steer with
                    <kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd>
                    or <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd>.
                </li>
                <li>On a phone or tablet, <b>swipe</b> on the board.</li>
                <li>
                    Eat the <span class="food-dot"></span> food to grow and earn
                    <b>10 points</b>.
                </li>
                <li>Don't hit the walls or your own tail.</li>
                <li><kbd>Space</kbd> or the Pause button pauses the game.</li>
                <li>If the keys don't respond, click once on the board.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------

def main() -> None:
    """Run the Snake Arena app."""

    gl.init_state(st.session_state)

    # Load embedded CSS instead of reading assets/style.css
    load_css()

    # Header

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

    # Stats placeholder
    stats_placeholder = st.empty()

    # Main layout
    board_col, side_col = st.columns([3, 2], gap="large")

    # Game board
    with board_col:
        difficulty = gl.get_difficulty(st.session_state.difficulty)
        state = st.session_state

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

        just_finished = (
            not finished_before
            and state.status in (gl.GAME_OVER, gl.WON)
        )

    # New record toast
    if just_finished and st.session_state.new_record:
        st.toast(
            f"New high score: {st.session_state.high_score}!",
            icon="🏆",
        )

    # Side panel
    with side_col:
        render_controls()

    # Render latest stats
    render_stats(stats_placeholder)

    # Footer
    st.markdown(
        f"""
        <div class="footer">
            Built with Python & Streamlit ·
            Games played this session: {st.session_state.games_played}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

main()
