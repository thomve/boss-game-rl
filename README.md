<div align="center">

<h1>⚔&nbsp; Boss Fight RL &nbsp;⚔</h1>

<p><strong>A turn-based boss fight where a Deep Q-Network learns to defeat the Dragon Lord from scratch.</strong></p>

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![Angular](https://img.shields.io/badge/Angular-21-DD0031?style=flat-square&logo=angular&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-backend-339933?style=flat-square&logo=node.js&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-only-013243?style=flat-square&logo=numpy)

</div>

---

## Overview

**Boss Fight RL** trains a DQN agent to fight a turn-based boss battle — abilities, cooldowns, mana, status effects and all — using a **pure NumPy neural network** (no PyTorch, no TensorFlow).

The project is split into three layers:

- **Python** — game engine, environment, DQN agent, and training script
- **Node.js backend** — Express + WebSocket server that spawns the Python training process and streams metrics in real time
- **Angular frontend** — web UI for training the agent, watching it play, and playing manually

---

## Features

- **Custom DQN** — experience replay, target network, epsilon-greedy with decay, action masking
- **Rich game mechanics** — 5 player abilities, 5 boss abilities, 6 status effects (poison, shield, stun, regen, enrage, weaken), mana & cooldown systems
- **Shaped reward function** — damage dealt, damage taken, HP advantage, DoT bonus, survival pressure
- **Web UI** — live training charts (avg reward, win rate), current metrics panel, Watch/Play mode
- **Real-time streaming** — training progress pushed over WebSocket; navigate away and come back without losing state
- **Zero heavy ML dependencies** — the entire agent and game engine run on NumPy only

---

## Project Structure

```
boss-game-rl/
├── game_engine.py        # Core game: Fighter, Ability, StatusEffect, BossFightGame
├── environment.py        # Gym-style wrapper: BossFightEnv
├── agent.py              # DQN: NeuralNetwork (NumPy) + DQNAgent
├── train.py              # Standalone training loop (CLI)
├── train_stream.py       # Streaming training loop (used by backend)
├── gui.py                # Pygame GUI (legacy Watch / Play modes)
├── trained_agent.json    # Serialised agent weights (generated after training)
├── pyproject.toml        # Python metadata & dependencies (uv)
│
├── backend/              # Node.js server
│   ├── src/
│   │   ├── index.js              # Express + WebSocket entry point (port 3000)
│   │   ├── websocket/handler.js  # Message routing
│   │   ├── training/manager.js   # Spawns train_stream.py, broadcasts metrics
│   │   └── game/                 # JS game state & agent loader
│   └── package.json
│
└── frontend/             # Angular 21 app
    ├── src/app/
    │   ├── training/     # Training page (config, live charts, metrics)
    │   ├── game/         # Game page (Watch / Play mode)
    │   ├── home/         # Home page
    │   └── services/     # WebsocketService, TrainingService, GameService
    └── package.json
```

---

## Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.12+ |
| Node.js | 18+ |
| npm | 9+ |

### 1 — Python environment

#### With uv (recommended)

```bash
# Install uv — Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install uv — macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
cd boss-game-rl
uv sync
```

#### With pip

```bash
cd boss-game-rl
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install numpy pygame
```

### 2 — Backend

```bash
cd backend
npm install
npm start          # or: npm run dev  (nodemon, auto-reload)
```

The backend listens on **http://localhost:3000** and **ws://localhost:3000**.

### 3 — Frontend

```bash
cd frontend
npm install
npm start          # serves on http://localhost:4200
```

Open **http://localhost:4200** in your browser.

---

## Usage

### Web UI

| Page | Path | What it does |
|------|------|--------------|
| Home | `/` | Overview and navigation |
| Training | `/training` | Configure episodes, start/stop training, live charts |
| Game | `/game` | Watch the trained agent play or play yourself |

**Training flow:**
1. Go to the Training page
2. Select the number of episodes (100 / 200 / 500 / 800)
3. Click **Start Training** — progress streams in real time via WebSocket
4. When complete, the agent is saved to `trained_agent.json` and auto-loaded in the Game page

### Standalone CLI training

```bash
# With uv
uv run python train.py

# With activated venv
python train.py
```

Training runs for 800 episodes and prints rolling metrics every 50 episodes:

```
Ep   50 | Avg Reward:   -3.41 | Win Rate:   5.0% | Avg Turns:  24.3 | Epsilon: 0.9653
Ep  200 | Avg Reward:    1.22 | Win Rate:  32.0% | Avg Turns:  31.7 | Epsilon: 0.8712
Ep  500 | Avg Reward:    4.87 | Win Rate:  61.0% | Avg Turns:  27.1 | Epsilon: 0.7093
Ep  800 | Avg Reward:    7.34 | Win Rate:  78.0% | Avg Turns:  22.8 | Epsilon: 0.5910
```

### Pygame GUI (legacy)

```bash
uv run python gui.py
```

Opens in **Watch mode** if `trained_agent.json` exists, otherwise **Play mode**.

| Control | Action |
|---------|--------|
| `R` | New game |
| `0` – `4` | Use ability (Play mode) |
| `Space` | Next turn |
| Click `Watch Agent` | Switch to agent mode |
| Click `Play Yourself` | Switch to player mode |
| Click `Auto: ON/OFF` | Toggle auto-advance |

---

## Architecture

### Game Engine

| Entity | Stats |
|--------|-------|
| **Hero** | 120 HP · 60 MP · 8 MP/turn · 5 abilities |
| **Dragon Lord** | 180 HP · 60 MP · 6 MP/turn · 5 abilities |
| **Turn limit** | 50 turns (timeout = loss) |

**Status effects:** `poison` · `shield` · `stunned` · `regen` · `enraged` · `weakened`

### Player Abilities

| # | Ability | Damage | Heal | Cost | Cooldown | Effect |
|---|---------|-------:|-----:|-----:|---------:|--------|
| 0 | Strike | 15 | — | 0 MP | — | — |
| 1 | Power Slash | 30 | — | 12 MP | 2 | — |
| 2 | Heal | — | 30 | 10 MP | 3 | — |
| 3 | Poison Blade | 10 | — | 8 MP | 3 | Poison 3t |
| 4 | Shield Up | — | — | 8 MP | 4 | Shield 2t (−50% dmg) |

### DQN Agent

```
State (20 dims)
  player_hp%, player_mp%, boss_hp%, boss_mp%, turn%
  player_cd × 5, boss_cd × 5
  player_poisoned, player_shielded, player_stunned, player_regen
  boss_poisoned, boss_enraged

Network: 20 → 256 → 128 → 5  (ReLU hidden, linear output)

Training:  lr=0.0008 · γ=0.97 · ε 1.0→0.05 · buffer=30k · batch=128
```

### Reward Shaping

| Event | Reward |
|-------|-------:|
| Damage dealt | `+2.0 × (dmg / boss_max_hp)` |
| Damage taken | `−1.5 × (dmg / player_max_hp)` |
| Defeat boss | `+10.0` |
| Player death | `−5.0` |
| Turn timeout | `−3.0` |
| HP advantage | `+0.1 × (player_hp% − boss_hp%)` |
| Apply poison DoT | `+0.3` |
| Player HP < 25% | `−0.2` |

### WebSocket Message Reference

| Direction | Message type | Payload |
|-----------|-------------|---------|
| Client → Server | `start_training` | `{ episodes: number }` |
| Client → Server | `stop_training` | — |
| Client → Server | `game_action` | `{ action: 0–4 }` |
| Client → Server | `game_reset` | — |
| Client → Server | `game_mode` | `{ mode: 'watch' \| 'play' }` |
| Server → Client | `training_started` | `{ episodes }` |
| Server → Client | `training_progress` | `{ data: { episode, total, avg_reward, win_rate, avg_turns, epsilon } }` |
| Server → Client | `training_complete` | — |
| Server → Client | `training_stopped` | — |
| Server → Client | `game_state` | full game state object |

---

## Dependencies

### Python

| Package | Purpose |
|---------|---------|
| `numpy` ≥ 2.4 | Neural network, state arrays |
| `pygame` ≥ 2.6 | Legacy Pygame GUI |

### Backend (Node.js)

| Package | Purpose |
|---------|---------|
| `express` ^4.18 | REST API |
| `ws` ^8.16 | WebSocket server |
| `cors` ^2.8 | CORS middleware |

### Frontend (Angular 21)

| Package | Purpose |
|---------|---------|
| `@angular/core` ^21.2 | Framework |
| `chart.js` ^4.5 | Training charts |
| `rxjs` ~7.8 | Reactive streams |

---

## License

MIT
