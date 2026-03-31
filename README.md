<div align="center">

<h1>⚔&nbsp; Boss Fight RL &nbsp;⚔</h1>

<p><strong>A turn-based boss fight where a Deep Q-Network learns to defeat the Dragon Lord from scratch.</strong></p>

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.6+-1A1A2E?style=flat-square)
![NumPy](https://img.shields.io/badge/NumPy-only-013243?style=flat-square&logo=numpy)
![uv](https://img.shields.io/badge/uv-managed-DE5FE9?style=flat-square)

</div>

---

## Overview

**Boss Fight RL** trains a DQN agent to fight a turn-based boss battle — abilities, cooldowns, mana, status effects and all — using a **pure NumPy neural network** (no PyTorch, no TensorFlow). Once trained, a **Pygame GUI** lets you watch the agent play in real time or take over the controls yourself.

```
┌──────────────────────┐     800 episodes     ┌──────────────────────┐
│   BossFightGame      │ ──────────────────▶  │   trained_agent.json │
│  turn-based engine   │                      │   DQN weights        │
└──────────────────────┘                      └──────────────────────┘
          │                                               │
          ▼                                               ▼
┌──────────────────────┐                      ┌──────────────────────┐
│   BossFightEnv       │                      │   Pygame GUI         │
│   Gym-like wrapper   │                      │   Watch or Play      │
└──────────────────────┘                      └──────────────────────┘
```

---

## Features

- **Custom DQN** — experience replay, target network, epsilon-greedy with decay, action masking
- **Rich game mechanics** — 5 player abilities, 5 boss abilities, 6 status effects (poison, shield, stun, regen, enrage, weaken), mana & cooldown systems
- **Shaped reward function** — damage dealt, damage taken, HP advantage, DoT bonus, survival pressure
- **Pygame GUI** — live HP/mana bars, combat log, Q-value bar chart, Watch/Play mode toggle
- **Zero heavy dependencies** — the entire agent and game engine run on NumPy only

---

## Quick Start

### With uv (recommended)

```bash
# Install uv if you haven't already
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
git clone <repo-url>
cd boss-game-rl

# Create venv and install dependencies in one step
uv sync

# Run the GUI
uv run python gui.py
```

### With pip

```bash
git clone <repo-url>
cd boss-game-rl

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install numpy pygame
python gui.py
```

---

## Usage

### Launch the GUI

```bash
uv run python gui.py
```

The GUI opens in **Watch mode** if `trained_agent.json` is present, or **Play mode** if it isn't.

| Control | Action |
|---------|--------|
| `R` | New game |
| `0` – `4` | Use ability (Play mode) |
| `Space` | Next turn (Watch / manual) |
| Click `Watch Agent` | Switch to agent mode |
| Click `Play Yourself` | Switch to player mode |
| Click `Auto: ON/OFF` | Toggle auto-advance |
| Click `New Game` | Reset |

### Train the agent

```bash
uv run python train.py
```

Training runs for 800 episodes and prints rolling metrics every 50 episodes:

```
Ep   50 | Avg Reward:   -3.41 | Win Rate:   5.0% | Avg Turns:  24.3 | Epsilon: 0.9653
Ep  200 | Avg Reward:    1.22 | Win Rate:  32.0% | Avg Turns:  31.7 | Epsilon: 0.8712
Ep  500 | Avg Reward:    4.87 | Win Rate:  61.0% | Avg Turns:  27.1 | Epsilon: 0.7093
Ep  800 | Avg Reward:    7.34 | Win Rate:  78.0% | Avg Turns:  22.8 | Epsilon: 0.5910
```

Weights are saved to `trained_agent.json` and full evaluation replays are printed as JSON on stdout.

---

## Project Structure

```
boss-game-rl/
├── game_engine.py      # Core game: Fighter, Ability, StatusEffect, BossFightGame
├── environment.py      # Gym-style wrapper: BossFightEnv
├── agent.py            # DQN: NeuralNetwork (NumPy) + DQNAgent
├── train.py            # Training loop + evaluation output
├── gui.py              # Pygame GUI (Watch / Play modes)
├── trained_agent.json  # Serialised agent weights
└── pyproject.toml      # Project metadata & dependencies (uv)
```

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

---

## GUI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  BOSS FIGHT RL          Turn 12 / 50                   Watch Agent  │  ← header
├──────────────┬──────────────────────────────┬──────────────────────┤
│  Hero        │  Combat Log                  │  Dragon Lord         │
│  HP ████░░░  │  === Turn 12 ===             │  HP ██████░░░░░░░░   │
│  MP ██████░  │    Hero uses Power Slash!    │  MP ████░░░░         │
│  Effects:    │    Dragon Lord takes 30 dmg  │  Effects:            │
│   shield(1t) │    Dragon Lord uses Enrage!  │   enraged(2t)        │
│  Abilities:  │    Hero takes 35 damage      │                      │
│  [0] Strike  │  === Turn 13 ===             │                      │
│  [1] Power…  │    ...                       │                      │
│  Q-chart ↓  │  ┌─────────────────────────┐ │                      │
│             │  │ Q-Values bar chart       │ │                      │
│             │  └─────────────────────────┘ │                      │
├──────────────┴──────────────────────────────┴──────────────────────┤
│  [ Strike ] [ Power Slash ] [  Heal  ] [ Poison Blade ] [Shield Up]│  ← ability btns
│  [Watch Agent] [Play Yourself] [Auto: ON] [Next Turn] [New Game]   │  ← controls
└─────────────────────────────────────────────────────────────────────┘
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | ≥ 2.4 | Neural network, state arrays |
| `pygame` | ≥ 2.6 | GUI rendering |

Python standard library only beyond those two.

---

## License

MIT
