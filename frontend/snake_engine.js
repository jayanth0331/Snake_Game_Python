/*
 * snake_engine.js - The pure rules of Snake.
 *
 * Nothing in this file draws anything or touches the web page. Every function
 * takes the current game and returns a NEW game object, which makes the rules
 * easy to understand and easy to test (see tests/test_snake_engine.js).
 *
 * Coordinates: {x, y} cells, (0, 0) is the top-left corner.
 * The snake is an array of cells, HEAD FIRST.
 */
(function (root) {
  "use strict";

  // How one move changes the head position for each direction.
  const DIRECTIONS = {
    up: { x: 0, y: -1 },
    down: { x: 0, y: 1 },
    left: { x: -1, y: 0 },
    right: { x: 1, y: 0 },
  };

  const OPPOSITE = { up: "down", down: "up", left: "right", right: "left" };

  // How many key presses we remember between two moves. Two lets a fast
  // player do a quick U-turn (e.g. Up then Left) without losing a key.
  const MAX_QUEUED_TURNS = 2;

  function isOpposite(a, b) {
    return OPPOSITE[a] === b;
  }

  function sameCell(a, b) {
    return a.x === b.x && a.y === b.y;
  }

  /* Pick a random empty cell for the food. Returns null if the board is full.
   * `rng` is a function returning a number in [0, 1); tests pass a fake one. */
  function spawnFood(snake, boardSize, rng) {
    rng = rng || Math.random;
    const occupied = new Set(snake.map((c) => c.x + "," + c.y));
    const freeCells = [];
    for (let y = 0; y < boardSize; y++) {
      for (let x = 0; x < boardSize; x++) {
        if (!occupied.has(x + "," + y)) freeCells.push({ x: x, y: y });
      }
    }
    if (freeCells.length === 0) return null;
    return freeCells[Math.floor(rng() * freeCells.length)];
  }

  /* A new game: the snake lies in the middle row, facing right. */
  function createGame(boardSize, initialLength, rng) {
    const middle = Math.floor(boardSize / 2);
    const snake = [];
    for (let i = 0; i < initialLength; i++) {
      snake.push({ x: middle - i, y: middle });
    }
    return {
      boardSize: boardSize,
      snake: snake,
      direction: "right",
      food: spawnFood(snake, boardSize, rng),
      score: 0,
      status: "running", // "running" | "over" | "won"
      lastEvent: "start", // what happened on the last step
    };
  }

  /* Add a key press to the queue of upcoming turns.
   * A turn is ignored if it reverses the snake (e.g. Left while moving Right,
   * which would make the snake crash into its own neck), repeats the same
   * direction, or the queue is already full. Returns the new queue. */
  function queueTurn(queue, currentDirection, newDirection) {
    if (!DIRECTIONS[newDirection]) return queue;
    const lastDirection = queue.length ? queue[queue.length - 1] : currentDirection;
    if (
      newDirection === lastDirection ||
      isOpposite(newDirection, lastDirection) ||
      queue.length >= MAX_QUEUED_TURNS
    ) {
      return queue;
    }
    return queue.concat([newDirection]);
  }

  /* Move the snake one cell. This is the heart of the game.
   *  1. Work out where the head goes next.
   *  2. Hitting a wall  -> game over.
   *  3. Hitting itself  -> game over.
   *  4. Landing on food -> grow, add points, spawn new food.
   *     Otherwise       -> move (drop the last tail cell). */
  function step(game, direction, pointsPerFood, rng) {
    if (game.status !== "running") return game;

    // Safety check: never allow an instant reverse, even if asked to.
    if (!DIRECTIONS[direction] || isOpposite(direction, game.direction)) {
      direction = game.direction;
    }

    const move = DIRECTIONS[direction];
    const head = game.snake[0];
    const newHead = { x: head.x + move.x, y: head.y + move.y };
    const size = game.boardSize;

    // 2. Wall collision: the new head is outside the board.
    if (newHead.x < 0 || newHead.y < 0 || newHead.x >= size || newHead.y >= size) {
      return Object.assign({}, game, { direction: direction, status: "over", lastEvent: "wall" });
    }

    // 3. Self collision. When the snake is NOT eating, its tail moves away
    // during this step, so moving into the current tail cell is allowed.
    const willEat = game.food !== null && sameCell(newHead, game.food);
    const body = willEat ? game.snake : game.snake.slice(0, -1);
    if (body.some((cell) => sameCell(cell, newHead))) {
      return Object.assign({}, game, { direction: direction, status: "over", lastEvent: "self" });
    }

    const snake = [newHead].concat(body);

    if (!willEat) {
      return Object.assign({}, game, { snake: snake, direction: direction, lastEvent: "move" });
    }

    // 4. Ate the food: score goes up, the snake is one cell longer.
    const food = spawnFood(snake, size, rng);
    return Object.assign({}, game, {
      snake: snake,
      direction: direction,
      score: game.score + pointsPerFood,
      food: food,
      status: food === null ? "won" : "running", // no free cell left = win
      lastEvent: "eat",
    });
  }

  const SnakeEngine = {
    DIRECTIONS: DIRECTIONS,
    MAX_QUEUED_TURNS: MAX_QUEUED_TURNS,
    isOpposite: isOpposite,
    spawnFood: spawnFood,
    createGame: createGame,
    queueTurn: queueTurn,
    step: step,
  };

  // Works in the browser (window.SnakeEngine) and in Node.js tests (require).
  if (typeof module !== "undefined" && module.exports) {
    module.exports = SnakeEngine;
  } else {
    root.SnakeEngine = SnakeEngine;
  }
})(this);
