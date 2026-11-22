/*
 * main.js - Runs the game board inside the Streamlit app.
 *
 * Sections:
 *   1. Talking to Streamlit (receive commands, send events back)
 *   2. Game loop (moves the snake at the chosen speed)
 *   3. Keyboard and swipe controls
 *   4. Drawing the board
 *
 * The rules themselves (moving, eating, crashing) are in snake_engine.js.
 */
(function () {
  "use strict";

  const Engine = window.SnakeEngine;
  const canvas = document.getElementById("board");
  const ctx = canvas.getContext("2d");
  const overlay = document.getElementById("overlay");

  // Settings sent by Python (game_logic.py). These are only fallbacks.
  let config = {
    board_size: 20,
    initial_length: 3,
    points_per_food: 10,
    tick_ms: 120,
    high_score: 0,
  };

  let status = "ready";     // "ready" | "running" | "paused" | "over" | "won"
  let game = null;          // current game object from snake_engine.js
  let turnQueue = [];       // upcoming direction changes
  let lastTickTime = 0;     // time of the last snake move (milliseconds)
  let gameId = null;        // which game this is (decided by Python)
  let lastCommandId = null; // last command from Python we already handled
  let mounted = false;      // becomes true on the first message from Streamlit
  let bestAtGameStart = 0;  // high score when the current game started

  // ===========================================================================
  // 1. Talking to Streamlit
  // ---------------------------------------------------------------------------
  // Streamlit custom components communicate with window.postMessage.
  // These message types are Streamlit's official component protocol:
  //   streamlit:componentReady    - "I'm loaded"          (board -> Streamlit)
  //   streamlit:render            - new values from Python (Streamlit -> board)
  //   streamlit:setComponentValue - send a value to Python (board -> Streamlit)
  //   streamlit:setFrameHeight    - resize the frame       (board -> Streamlit)
  // ===========================================================================
  function sendToStreamlit(type, data) {
    window.parent.postMessage(Object.assign({ isStreamlitMessage: true, type: type }, data), "*");
  }

  // Each loaded board gets a random id so its event ids are always unique.
  const boardSessionId = Math.random().toString(36).slice(2, 8);
  let eventCounter = 0;

  /* Tell Python something happened. This makes Streamlit re-run app.py,
   * where game_logic.apply_board_event() reads this value. */
  function sendEvent(type) {
    eventCounter += 1;
    sendToStreamlit("streamlit:setComponentValue", {
      dataType: "json",
      value: {
        id: boardSessionId + "-" + eventCounter,
        type: type,
        score: game ? game.score : 0,
        game_id: gameId,
      },
    });
  }

  function updateFrameHeight() {
    sendToStreamlit("streamlit:setFrameHeight", {
      height: Math.ceil(document.body.getBoundingClientRect().height) + 4,
    });
  }

  window.addEventListener("message", function (event) {
    const msg = event.data;
    if (msg && msg.type === "streamlit:render") onRender(msg.args || {});
  });

  /* Called every time app.py runs. `args` are the values Python passed. */
  function onRender(args) {
    for (const key of Object.keys(config)) {
      if (typeof args[key] === "number") config[key] = args[key];
    }

    if (!mounted) {
      // First load: don't replay an old command. Show "ready" and tell
      // Python so both sides agree that no game is running.
      mounted = true;
      lastCommandId = args.command_id;
      sendEvent("ready");
    } else if (args.command_id !== lastCommandId) {
      // A NEW command (Start / Pause / Resume) from a Streamlit button.
      lastCommandId = args.command_id;
      handleCommand(args.command, args.game_id);
    }
    updateOverlay();
    updateFrameHeight();
  }

  function handleCommand(command, newGameId) {
    if (command === "start") {
      gameId = newGameId;
      bestAtGameStart = config.high_score; // used for the "new high score" badge
      game = Engine.createGame(config.board_size, config.initial_length);
      turnQueue = [];
      status = "running";
      lastTickTime = performance.now();
      canvas.focus({ preventScroll: true });
    } else if (command === "pause" && status === "running") {
      status = "paused";
    } else if (command === "resume" && status === "paused") {
      status = "running";
      lastTickTime = performance.now();
    }
  }

  // ===========================================================================
  // 2. Game loop
  // ---------------------------------------------------------------------------
  // requestAnimationFrame calls `frame` about 60 times per second. The snake
  // only moves when `tick_ms` milliseconds have passed, so the difficulty
  // controls the speed, while the drawing (e.g. glowing food) stays smooth.
  // ===========================================================================
  function frame(now) {
    if (status === "running" && now - lastTickTime >= config.tick_ms) {
      lastTickTime = now;
      tick();
    }
    draw(now);
    requestAnimationFrame(frame);
  }

  /* One snake move. */
  function tick() {
    const direction = turnQueue.length ? turnQueue.shift() : game.direction;
    game = Engine.step(game, direction, config.points_per_food);

    if (game.lastEvent === "eat") sendEvent(game.status === "won" ? "won" : "score");
    if (game.status === "over") {
      status = "over";
      sendEvent("over");
    } else if (game.status === "won") {
      status = "won";
    }
    if (status !== "running") updateOverlay();
  }

  function togglePauseFromKeyboard() {
    if (status === "running") {
      status = "paused";
      sendEvent("pause");
    } else if (status === "paused") {
      status = "running";
      lastTickTime = performance.now();
      sendEvent("resume");
    }
    updateOverlay();
  }

  // ===========================================================================
  // 3. Keyboard and swipe controls
  // ===========================================================================
  const KEY_TO_DIRECTION = {
    ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right",
    w: "up", s: "down", a: "left", d: "right",
    W: "up", S: "down", A: "left", D: "right",
  };

  function onKeyDown(event) {
    // Don't steal keys while the user is typing in a text box.
    const target = event.target;
    const tag = target && target.tagName ? target.tagName.toLowerCase() : "";
    const isTyping =
      tag === "textarea" || tag === "select" || (target && target.isContentEditable) ||
      (tag === "input" && !["radio", "checkbox", "button"].includes(target.type));
    if (isTyping) return;

    const playing = status === "running" || status === "paused";
    const direction = KEY_TO_DIRECTION[event.key];

    if (direction) {
      if (playing) event.preventDefault(); // stop the page from scrolling
      if (status === "running") {
        turnQueue = Engine.queueTurn(turnQueue, game.direction, direction);
      }
    } else if (event.key === " " && playing) {
      event.preventDefault();
      togglePauseFromKeyboard();
    } else {
      return;
    }

    // If a Streamlit button still has keyboard focus, Space would also
    // "click" it. Removing the focus prevents that double action.
    const active = target && target.ownerDocument && target.ownerDocument.activeElement;
    if (active && active.tagName === "BUTTON") active.blur();
  }

  window.addEventListener("keydown", onKeyDown);

  // After clicking a Streamlit button, the keyboard focus is on the main page,
  // not on this frame. So we also listen on the main page. This works because
  // Streamlit serves components from the same website (same origin). If the
  // browser blocks it, the player can simply click the board first.
  let parentDocument = null;
  try {
    parentDocument = window.parent.document;
    // Remove a listener left behind by an older copy of this board.
    if (window.parent.__snakeArenaKeyHandler) {
      parentDocument.removeEventListener("keydown", window.parent.__snakeArenaKeyHandler);
    }
    parentDocument.addEventListener("keydown", onKeyDown);
    window.parent.__snakeArenaKeyHandler = onKeyDown;
  } catch (error) {
    parentDocument = null; // cross-origin: keyboard works after clicking the board
  }

  window.addEventListener("pagehide", function () {
    if (parentDocument) {
      parentDocument.removeEventListener("keydown", onKeyDown);
      if (window.parent.__snakeArenaKeyHandler === onKeyDown) {
        window.parent.__snakeArenaKeyHandler = null;
      }
    }
  });

  // Swipe controls for phones and tablets.
  let touchStart = null;
  canvas.addEventListener("touchstart", function (event) {
    const t = event.changedTouches[0];
    touchStart = { x: t.clientX, y: t.clientY };
  }, { passive: true });

  canvas.addEventListener("touchend", function (event) {
    if (!touchStart || status !== "running") return;
    const t = event.changedTouches[0];
    const dx = t.clientX - touchStart.x;
    const dy = t.clientY - touchStart.y;
    touchStart = null;
    if (Math.max(Math.abs(dx), Math.abs(dy)) < 24) return; // too short: a tap
    const direction = Math.abs(dx) > Math.abs(dy)
      ? (dx > 0 ? "right" : "left")
      : (dy > 0 ? "down" : "up");
    turnQueue = Engine.queueTurn(turnQueue, game.direction, direction);
  }, { passive: true });

  // ===========================================================================
  // 4. Drawing the board
  // ===========================================================================
  const COLORS = {
    background: "#070b14",
    gridLine: "rgba(120, 150, 200, 0.08)",
    snakeHead: "#7dff5c",
    snakeTail: "#14a800",
    glow: "rgba(57, 255, 20, 0.65)",
    food: "#ff5a36",
    foodGlow: "rgba(255, 90, 54, 0.8)",
    eye: "#06210a",
  };

  /* Make the canvas sharp on high-resolution screens. */
  function resizeCanvas() {
    const cssSize = canvas.getBoundingClientRect().width;
    const pixels = Math.round(cssSize * (window.devicePixelRatio || 1));
    if (canvas.width !== pixels) {
      canvas.width = pixels;
      canvas.height = pixels;
    }
  }

  function roundedRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  /* Mix two hex colours: t = 0 gives `a`, t = 1 gives `b`. */
  function mixColor(a, b, t) {
    const pa = parseInt(a.slice(1), 16);
    const pb = parseInt(b.slice(1), 16);
    const channel = (shift) =>
      Math.round(((pa >> shift) & 255) * (1 - t) + ((pb >> shift) & 255) * t);
    return "rgb(" + channel(16) + "," + channel(8) + "," + channel(0) + ")";
  }

  function draw(now) {
    resizeCanvas();
    const size = canvas.width;
    const n = config.board_size;
    const cell = size / n;

    // Background
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, size, size);

    // Grid lines
    ctx.strokeStyle = COLORS.gridLine;
    ctx.lineWidth = Math.max(1, size / 600);
    ctx.beginPath();
    for (let i = 1; i < n; i++) {
      const p = Math.round(i * cell) + 0.5;
      ctx.moveTo(p, 0); ctx.lineTo(p, size);
      ctx.moveTo(0, p); ctx.lineTo(size, p);
    }
    ctx.stroke();

    if (!game) return;

    // Food: a glowing circle that gently pulses.
    if (game.food) {
      const pulse = 0.5 + 0.5 * Math.sin(now / 220);
      const cx = (game.food.x + 0.5) * cell;
      const cy = (game.food.y + 0.5) * cell;
      ctx.save();
      ctx.shadowColor = COLORS.foodGlow;
      ctx.shadowBlur = cell * (0.5 + 0.4 * pulse);
      ctx.fillStyle = COLORS.food;
      ctx.beginPath();
      ctx.arc(cx, cy, cell * (0.3 + 0.04 * pulse), 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // Snake: drawn from tail to head so the head is on top.
    const pad = cell * 0.08;
    const length = game.snake.length;
    ctx.save();
    ctx.shadowColor = COLORS.glow;
    for (let i = length - 1; i >= 0; i--) {
      const part = game.snake[i];
      ctx.shadowBlur = i === 0 ? cell * 0.8 : cell * 0.35;
      ctx.fillStyle = mixColor(COLORS.snakeHead, COLORS.snakeTail, length > 1 ? i / (length - 1) : 0);
      roundedRect(part.x * cell + pad, part.y * cell + pad, cell - pad * 2, cell - pad * 2, cell * 0.28);
      ctx.fill();
    }
    ctx.restore();

    drawEyes(game.snake[0], game.direction, cell);
  }

  function drawEyes(head, direction, cell) {
    const move = Engine.DIRECTIONS[direction];
    const cx = (head.x + 0.5) * cell;
    const cy = (head.y + 0.5) * cell;
    const forward = cell * 0.18;
    const side = cell * 0.18;
    ctx.fillStyle = COLORS.eye;
    for (const s of [-1, 1]) {
      // Eyes sit forward of the centre, spread sideways from the direction.
      const ex = cx + move.x * forward + (-move.y) * side * s;
      const ey = cy + move.y * forward + move.x * side * s;
      ctx.beginPath();
      ctx.arc(ex, ey, cell * 0.08, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  /* The text panel over the board for Ready / Paused / Game Over / Win. */
  function updateOverlay() {
    const score = game ? game.score : 0;
    const best = Math.max(config.high_score, score);
    let html = "";
    let danger = false;

    if (status === "ready") {
      html =
        "<h2>SNAKE ARENA</h2>" +
        "<p class='big'>Press <b>Start Game</b> to play</p>" +
        "<p>Move with <kbd>↑</kbd> <kbd>↓</kbd> <kbd>←</kbd> <kbd>→</kbd> or <kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd>" +
        " &nbsp;·&nbsp; <kbd>Space</kbd> to pause</p>";
    } else if (status === "paused") {
      html =
        "<h2>PAUSED</h2>" +
        "<p class='big'>Score: " + score + "</p>" +
        "<p>Press <kbd>Space</kbd> or <b>Resume</b> to continue</p>";
    } else if (status === "over") {
      danger = true;
      html =
        "<h2>GAME OVER</h2>" +
        "<p class='big'>Score: " + score + "</p>" +
        "<p>Best: " + best + "</p>" +
        (score > bestAtGameStart ? "<span class='badge'>NEW HIGH SCORE!</span>" : "") +
        "<p>Press <b>Restart Game</b> to try again</p>";
    } else if (status === "won") {
      html =
        "<h2>YOU WIN!</h2>" +
        "<p class='big'>Score: " + score + "</p>" +
        "<p>You filled the entire board. Press <b>Restart Game</b> to play again.</p>";
    }

    overlay.innerHTML = html;
    overlay.classList.toggle("hidden", status === "running");
    overlay.classList.toggle("danger", danger);
  }

  // Keep the frame height right when the window is resized.
  window.addEventListener("resize", updateFrameHeight);

  // Start everything.
  updateOverlay();
  requestAnimationFrame(frame);
  sendToStreamlit("streamlit:componentReady", { apiVersion: 1 });
  updateFrameHeight();
})();
