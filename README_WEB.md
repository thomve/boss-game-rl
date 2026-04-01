# Boss Fight RL — Web Application

A full Angular + Node.js web interface for the Boss Fight reinforcement learning project.

## Quick Start

### Windows
```
start.bat
```

### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

Then open **http://localhost:4200** in your browser.

---

## Manual Setup

### Backend (Node.js)
```bash
cd backend
npm install
npm start          # production
npm run dev        # with nodemon auto-reload
```
Backend runs on **http://localhost:3000**

### Frontend (Angular)
```bash
cd frontend
npm install
npm start          # ng serve on port 4200
```
Frontend runs on **http://localhost:4200**

---

## Requirements

- **Node.js 18+** — for backend + frontend build
- **Python 3.8+** with **numpy** — only needed for training
- The frontend and game engine run entirely in Node.js (no Python needed to play or watch)

---

## Features

| Page | Description |
|------|-------------|
| **Home** | Landing page showing agent status and navigation |
| **Watch Agent** | Observe the DQN agent fight the Dragon Lord in real-time |
| **Play Yourself** | Control the Hero manually |
| **Training** | Start/stop training with live charts (reward, win rate) |

---

## Architecture

```
boss-game-rl/
├── train_stream.py          # Python training script (JSON-line stdout)
├── backend/
│   └── src/
│       ├── index.js         # Express + WebSocket server (port 3000)
│       ├── game/
│       │   ├── engine.js    # Full JS port of game_engine.py
│       │   ├── agent.js     # DQN inference in pure JS
│       │   └── manager.js   # Game session manager
│       ├── training/
│       │   └── manager.js   # Python subprocess manager
│       └── websocket/
│           └── handler.js   # WS message dispatcher
└── frontend/
    └── src/app/
        ├── home/            # Landing page
        ├── game/            # Game view + sub-components
        ├── training/        # Training dashboard
        └── services/        # WS, Game, Training services
```

---

## WebSocket API

All communication uses WebSocket on `ws://localhost:3000`.

**Client → Server:**
| Message | Description |
|---------|-------------|
| `{type: "game_action", action: N}` | Perform hero ability N (0–4) |
| `{type: "game_reset"}` | Reset the game |
| `{type: "game_mode", mode: "watch"\|"play"}` | Switch mode |
| `{type: "agent_step"}` | Let agent take one step |
| `{type: "start_training", episodes: N}` | Start training |
| `{type: "stop_training"}` | Stop training |

**Server → Client:**
| Message | Description |
|---------|-------------|
| `{type: "game_state", state: {...}}` | Full game state after every action |
| `{type: "training_progress", data: {...}}` | Training metrics every 10 episodes |
| `{type: "training_complete", data: {...}}` | Training finished |
| `{type: "agent_status", hasAgent: bool}` | Whether weights are loaded |
