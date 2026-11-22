# 🐍 Snake Arena

**Snake Arena** is the classic Snake game, built with **Python** and **Streamlit**, with a modern dark arcade look.
Steer the neon-green snake, eat the glowing food, grow longer, and try to beat your high score without hitting a wall or your own tail.

It runs in any web browser and can be published **for free** on Streamlit Community Cloud. No paid API, database or hosting is needed.

---

## 📑 Table of Contents

1. [Project Objectives](#-project-objectives)
2. [Features](#-features)
3. [Technologies Used](#-technologies-used)
4. [Screenshots](#-screenshots)
5. [Project Folder Structure](#-project-folder-structure)
6. [How It Works](#-how-it-works)
7. [Installation](#-installation)
8. [How to Run Locally](#-how-to-run-locally)
9. [Game Controls](#-game-controls)
10. [Running the Tests](#-running-the-tests)
11. [Upload to GitHub](#-upload-to-github)
12. [Deploy on Streamlit Community Cloud](#-deploy-on-streamlit-community-cloud)
13. [Limitations](#-limitations)
14. [Troubleshooting](#-troubleshooting)

---

## 🎯 Project Objectives

- Build a complete, playable game using Python and Streamlit.
- Learn how **Streamlit session state** keeps data (score, high score) between re-runs.
- Keep the **game rules separate from the user interface**.
- Learn how a Streamlit app can talk to a small **JavaScript component** for real-time features.
- Write **automated tests** for the game rules.
- Publish the code on **GitHub** and deploy the live game on **Streamlit Community Cloud** for free.

---

## ✨ Features

| Area | What it does |
|---|---|
| **Movement** | The snake moves on its own. Steer with the **Arrow keys** or **W A S D**, or **swipe** on phones. |
| **No instant reverse** | Pressing the opposite direction (e.g. Left while moving Right) is ignored, so you can't crash into your own neck by mistake. |
| **Food** | Appears on a random empty cell. It **never** appears on the snake. |
| **Scoring** | **+10 points** for every food. |
| **High score** | Kept in `st.session_state` and stays while the browser tab is open. |
| **Collisions** | Hitting any of the **4 walls** or the snake's **own body** ends the game. |
| **Game Over screen** | Shows your score, your best score and a "NEW HIGH SCORE!" badge. |
| **Difficulty** | **Easy** (5.6 moves/s), **Medium** (8.3 moves/s), **Hard** (13.3 moves/s). |
| **Controls** | Start, Pause / Resume (button or **Space**), Restart. |
| **Design** | Dark arcade theme, neon snake, glowing food, grid board, rounded cards and buttons. Works on phones too. |

---

## 🛠 Technologies Used

| Technology | Used for |
|---|---|
| **Python 3.10+** | App logic and session-state rules |
| **Streamlit** | Web app framework (layout, buttons, session state) |
| **HTML + CSS** | Page styling and the game board |
| **JavaScript** | Real-time game loop, keyboard controls and drawing |
| **Git + GitHub** | Storing and sharing the source code |
| **Streamlit Community Cloud** | Free hosting of the playable game |

The only Python package needed is `streamlit`.

---

## 📸 Screenshots

| Playing | Game Over |
|---|---|
| ![Gameplay](assets/screenshots/gameplay.png) | ![Game Over](assets/screenshots/game-over.png) |

**To add or replace screenshots:**

1. Run the game (see [How to Run Locally](#-how-to-run-locally)).
2. Take a screenshot:
   - **Windows:** `Win + Shift + S`
   - **macOS:** `Cmd + Shift + 4`
   - **Linux:** `PrtSc` or the Screenshot app
3. Save the image as a `.png` file inside the `assets/screenshots/` folder, for example `assets/screenshots/my-screenshot.png`.
4. Show it in this README with a line like this:
   ```markdown
   ![My screenshot](assets/screenshots/my-screenshot.png)
   ```

---

## 📁 Project Folder Structure

```
snake-game/
│
├── app.py                    # Streamlit app: page layout, score cards, buttons
├── game_logic.py             # Settings + session-state rules (no UI code)
├── requirements.txt          # Python packages to install (just streamlit)
├── README.md                 # This file
├── .gitignore                # Files Git should NOT upload
│
├── .streamlit/
│   └── config.toml           # Dark theme colours for Streamlit
│
├── assets/
│   ├── style.css             # Arcade styling for the page
│   └── screenshots/          # Images used in this README
│
├── frontend/                 # The game board (runs in the browser)
│   ├── index.html            # Board page: canvas + overlay messages
│   ├── snake_engine.js       # Pure game rules: move, eat, collide
│   └── main.js               # Game loop, drawing, keyboard, Streamlit link
│
└── tests/
    ├── test_game_logic.py    # Python tests (scores, pause, high score...)
    └── test_snake_engine.js  # JavaScript tests (movement, food, collisions)
```

---

## ⚙️ How It Works

### Why is there JavaScript in a Python project?

Every time you click something in Streamlit, **the whole Python script runs again on the server**. That's fine for buttons, but a snake must move about 10 times per second. If Python moved the snake, every move would need a trip to the server and back, so the game would lag and miss key presses, especially once it's online.

So the work is split:

| Part | Runs in | Responsible for |
|---|---|---|
| `app.py` + `game_logic.py` | **Python (server)** | Layout, buttons, difficulty, score, high score, game status (`st.session_state`) |
| `frontend/` | **JavaScript (browser)** | Moving the snake, reading keys, drawing the board |

They talk using Streamlit's official **custom component** messages:

```
   Python (app.py)                                Browser (frontend/)
 ┌──────────────────────┐   settings + command   ┌──────────────────────┐
 │ Start / Pause button │ ─────────────────────▶ │ starts / pauses game │
 │                      │                        │                      │
 │ updates score and    │ ◀───────────────────── │ "ate food", "crashed"│
 │ high score in        │   event (score, type)  │                      │
 │ st.session_state     │                        │                      │
 └──────────────────────┘                        └──────────────────────┘
```

### The game logic, step by step

1. **Start:** you click **Start Game**. `game_logic.start_game()` sets the score to 0 and the status to "running", and stores a `"start"` command with a new **command id**.
2. **Command arrives:** Streamlit re-runs `app.py`, which passes the command to the board. The board sees a new command id and creates a new game: a 3-cell snake in the middle, facing right, plus food on a random empty cell.
3. **Game loop:** about 60 times a second the board redraws. Every `tick_ms` milliseconds (180 / 120 / 75 depending on difficulty) it moves the snake one step with `SnakeEngine.step()`:
   - Work out the new head position from the direction.
   - **Outside the board?** → wall collision → game over.
   - **On the snake's body?** → self collision → game over. (The tail cell counts as free, because the tail moves away in the same step.)
   - **On the food?** → the snake keeps its tail (grows by 1), the score goes up by 10 and new food appears on an empty cell.
   - **Otherwise** → add the new head and remove the last tail cell (the snake moves).
4. **Keys:** each key press is checked by `queueTurn()`. Reversing directly and repeated presses are ignored. Up to 2 turns are remembered so quick turns aren't lost.
5. **Reporting back:** when the snake eats or crashes, the board sends an event such as `{"type": "score", "score": 30}` to Python. `game_logic.apply_board_event()` checks it and updates the score, high score and status. The score cards then refresh.
6. **Game over:** the board shows the Game Over screen and Python updates the high score.

### Important decisions (useful for your presentation)

- **Session state:** `init_state()` only creates keys that don't exist yet, so the score and high score survive Streamlit's re-runs.
- **Command ids:** Streamlit sends the board the same values on every re-run. The increasing `command_id` lets the board tell a *new* click from an old one.
- **Event ids:** Streamlit keeps returning the board's *last* event on every re-run. Python remembers the last event id, so an event is never counted twice.
- **Game ids:** if you press Restart just as the snake eats, the late "ate food" message belongs to the old game. It carries the old game id and is ignored.
- **Score check:** Python only accepts scores that are whole multiples of 10 and within the possible range.
- **Difficulty lock:** the difficulty can't be changed during a game, so the speed never changes mid-game.
- **Keyboard focus:** after clicking a Streamlit button, the keyboard focus is on the main page, not on the board. The board therefore also listens to key presses on the main page, so you don't have to click the board after every button.
- **No build tools:** the component is plain HTML and JavaScript. There is no Node.js or npm build step, so deployment is simple.

---

## 💻 Installation

### 1. Install Python

Download Python **3.10 or newer** from [python.org](https://www.python.org/downloads/).
On Windows, tick **"Add Python to PATH"** during installation.

Check it works by opening a terminal (Command Prompt / PowerShell on Windows, Terminal on macOS/Linux):

```bash
python --version
```

> On macOS/Linux you may need to type `python3` instead of `python` (and `pip3` instead of `pip`).

### 2. Get the project

Either download the project folder, or clone it from GitHub:

```bash
git clone https://github.com/<your-username>/snake-game.git
cd snake-game
```

### 3. Create a virtual environment (recommended)

A virtual environment keeps this project's packages separate from other projects.

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You'll see `(.venv)` at the start of your terminal line when it's active.

### 4. Install the dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run Locally

From inside the project folder (with the virtual environment active):

```bash
streamlit run app.py
```

Your browser opens at **http://localhost:8501**. If it doesn't, open that address yourself.
To stop the app, press `Ctrl + C` in the terminal.

---

## 🎮 Game Controls

| Action | Keyboard | Phone / tablet | Button |
|---|---|---|---|
| Move up | `↑` or `W` | Swipe up | – |
| Move down | `↓` or `S` | Swipe down | – |
| Move left | `←` or `A` | Swipe left | – |
| Move right | `→` or `D` | Swipe right | – |
| Pause / Resume | `Space` | – | **Pause / Resume** |
| Start a game | – | – | **Start Game** |
| Start over | – | – | **Restart Game** |
| Change speed | – | – | **Easy / Medium / Hard** (when no game is running) |

**Tip:** if the keys don't respond, click once on the game board.

---

## 🧪 Running the Tests

The project includes automated tests. They use only built-in tools, so there is nothing extra to install.

**Python tests** (session state, scoring, high score, pause, restart, difficulty):

```bash
python -m unittest discover tests
```

**JavaScript tests** (movement, food generation, wall and self collisions, winning). These need [Node.js](https://nodejs.org/) 18 or newer, but only for testing. The game itself does not need Node.js.

```bash
node --test tests/test_snake_engine.js
```

---

## 🌐 Upload to GitHub

GitHub **stores your source code**. (The playable game is hosted by Streamlit Community Cloud. See the next section.)

1. Create a free account at [github.com](https://github.com/) and install [Git](https://git-scm.com/downloads).
2. Tell Git who you are (only needed once per computer):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```
3. On GitHub, click **+** (top right) → **New repository**.
   - Name: `snake-game`
   - Visibility: **Public** (simplest for Streamlit Community Cloud)
   - Do **not** tick "Add a README" (we already have one)
   - Click **Create repository**.
4. In a terminal **inside the project folder**, run:
   ```bash
   git init
   git add .
   git commit -m "First version of Snake Arena"
   git branch -M main
   git remote add origin https://github.com/<your-username>/snake-game.git
   git push -u origin main
   ```
   Replace `<your-username>` with your GitHub username. When Git asks for a password, use a **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens), not your account password.
5. Refresh the GitHub page. Your files are now online.
   The `.gitignore` file makes sure the `.venv` folder and cache files are **not** uploaded.

**Later changes:** after editing files, upload them again with:

```bash
git add .
git commit -m "Describe what you changed"
git push
```

---

## ☁️ Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/) and **sign in with GitHub**.
2. Click **Create app** → **Deploy a public app from GitHub** (wording may vary slightly).
3. Fill in:
   - **Repository:** `<your-username>/snake-game`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** choose a name, e.g. `snake-arena-yourname`
4. (Optional) Under **Advanced settings**, choose Python **3.12**.
5. Click **Deploy**. The first start takes a minute or two while `streamlit` is installed from `requirements.txt`.
6. You get a public link like `https://snake-arena-yourname.streamlit.app`. Share it with your teacher and friends!

Every time you `git push` new changes, the app updates automatically.

> **Note:** free apps "sleep" after a period without visitors. The first visitor then clicks a button to wake it up, which takes a few seconds.

---

## ⚠️ Limitations

- **High score is per browser session.** It's kept in `st.session_state`, so it resets when the tab is refreshed or closed. A permanent leaderboard would need a database, which this project deliberately avoids.
- **The snake runs in the browser.** Python manages the game state, but the moving itself happens in JavaScript, because a server round-trip for every move would make the game lag online.
- **Score updates go through Streamlit.** The score cards refresh after a short server round-trip (usually a fraction of a second online). The board itself is never delayed.
- **Keyboard focus.** In rare browser setups the board can't listen to keys on the main page; clicking the board once fixes it.
- **Not cheat-proof.** Python checks that scores look valid, but someone with browser developer tools could still fake a score. That's acceptable for a session-only high score.
- **Phones:** swipes work on the board, but you need to scroll down to reach the buttons on a small screen.

---

## 🩺 Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Activate the virtual environment, or run `python -m streamlit run app.py`. |
| `ModuleNotFoundError: No module named 'streamlit'` | Run `pip install -r requirements.txt` with the virtual environment active. |
| Arrow keys scroll the page instead of moving the snake | Click once on the game board. |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Deployment fails on Streamlit Cloud | Check that **Main file path** is `app.py` and that `requirements.txt` is in the repository root. |

---

Made with ❤️ using Python and Streamlit.
