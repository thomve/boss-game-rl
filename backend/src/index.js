'use strict';

const express = require('express');
const cors = require('cors');
const http = require('http');
const { WebSocketServer } = require('ws');
const path = require('path');

const { GameManager } = require('./game/manager');
const { TrainingManager } = require('./training/manager');
const { handleMessage } = require('./websocket/handler');

const PORT = process.env.PORT || 3000;

// ─── App Setup ─────────────────────────────────────────────────────────────
const app = express();
app.use(cors());
app.use(express.json());

// Singleton managers
const gameManager = new GameManager();
const trainingManager = new TrainingManager();
const wsClients = new Set();

// ─── REST Routes ───────────────────────────────────────────────────────────
app.get('/api/agent/status', (req, res) => {
  res.json({
    hasAgent: gameManager.hasAgent(),
    mode: gameManager.mode,
  });
});

app.post('/api/training/start', (req, res) => {
  const episodes = parseInt(req.body.episodes) || 800;
  const result = trainingManager.startTraining(episodes, undefined, wsClients, (data) => {
    setTimeout(() => gameManager.reloadAgent(), 500);
  });
  res.json(result);
});

app.post('/api/training/stop', (req, res) => {
  const result = trainingManager.stopTraining();
  res.json(result);
});

app.get('/api/training/status', (req, res) => {
  res.json({ isTraining: trainingManager.isTraining() });
});

app.get('/api/game/state', (req, res) => {
  res.json(gameManager.getStatus());
});

// ─── HTTP + WebSocket Server ───────────────────────────────────────────────
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
  wsClients.add(ws);
  console.log(`[WS] Client connected. Total: ${wsClients.size}`);

  // Send initial state on connect
  const state = gameManager._buildResponse();
  ws.send(JSON.stringify({ type: 'game_state', state }));
  ws.send(JSON.stringify({ type: 'agent_status', hasAgent: gameManager.hasAgent() }));

  ws.on('message', (raw) => {
    handleMessage(ws, raw.toString(), gameManager, trainingManager, wsClients);
  });

  ws.on('close', () => {
    wsClients.delete(ws);
    console.log(`[WS] Client disconnected. Total: ${wsClients.size}`);
  });

  ws.on('error', (err) => {
    console.error('[WS] Error:', err.message);
    wsClients.delete(ws);
  });
});

server.listen(PORT, () => {
  console.log(`Boss Fight RL backend running on http://localhost:${PORT}`);
  console.log(`WebSocket available at ws://localhost:${PORT}`);
  console.log(`Agent loaded: ${gameManager.hasAgent()}`);
});
