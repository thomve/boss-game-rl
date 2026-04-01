'use strict';

/**
 * WebSocket message handler.
 * Handles all client <-> server game and training messages.
 */
function handleMessage(ws, rawMessage, gameManager, trainingManager, wsClients) {
  let msg;
  try {
    msg = JSON.parse(rawMessage);
  } catch (e) {
    ws.send(JSON.stringify({ type: 'error', message: 'Invalid JSON' }));
    return;
  }

  switch (msg.type) {
    case 'game_action': {
      const action = typeof msg.action === 'number' ? msg.action : 0;
      const state = gameManager.playerAction(action);
      ws.send(JSON.stringify({ type: 'game_state', state }));
      break;
    }

    case 'game_reset': {
      const state = gameManager.reset();
      ws.send(JSON.stringify({ type: 'game_state', state }));
      break;
    }

    case 'game_mode': {
      const mode = msg.mode === 'play' ? 'play' : 'watch';
      gameManager.setMode(mode);
      ws.send(JSON.stringify({ type: 'mode_changed', mode }));
      break;
    }

    case 'agent_step': {
      const state = gameManager.agentStep();
      ws.send(JSON.stringify({ type: 'game_state', state }));
      break;
    }

    case 'agent_status': {
      ws.send(JSON.stringify({
        type: 'agent_status',
        hasAgent: gameManager.hasAgent(),
      }));
      break;
    }

    case 'start_training': {
      const episodes = typeof msg.episodes === 'number' ? msg.episodes : 800;
      const result = trainingManager.startTraining(episodes, undefined, wsClients, (completeData) => {
        // Reload agent after training completes
        setTimeout(() => gameManager.reloadAgent(), 500);
      });
      ws.send(JSON.stringify({ type: 'training_started', ...result, episodes }));
      break;
    }

    case 'stop_training': {
      const result = trainingManager.stopTraining();
      ws.send(JSON.stringify({ type: 'training_stopped', ...result }));
      break;
    }

    default:
      ws.send(JSON.stringify({ type: 'error', message: `Unknown message type: ${msg.type}` }));
  }
}

module.exports = { handleMessage };
