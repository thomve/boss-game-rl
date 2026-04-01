'use strict';

const { spawn } = require('child_process');
const path = require('path');

const SCRIPT_PATH = path.resolve(__dirname, '../../../train_stream.py');
const DEFAULT_OUTPUT = path.resolve(__dirname, '../../../trained_agent.json');

class TrainingManager {
  constructor() {
    this._process = null;
    this._isTraining = false;
  }

  isTraining() {
    return this._isTraining;
  }

  /**
   * Start training subprocess.
   * @param {number} episodes
   * @param {string} outputPath
   * @param {Set<WebSocket>} wsClients
   * @param {Function} onComplete - called with final data when done
   */
  startTraining(episodes = 800, outputPath = DEFAULT_OUTPUT, wsClients = new Set(), onComplete = null) {
    if (this._isTraining) {
      return { success: false, message: 'Training already in progress' };
    }

    // Try python, then python3
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

    this._isTraining = true;
    this._process = spawn(pythonCmd, [
      SCRIPT_PATH,
      '--episodes', String(episodes),
      '--output', outputPath,
    ], {
      cwd: path.dirname(SCRIPT_PATH),
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let buffer = '';

    this._process.stdout.on('data', (chunk) => {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
          const data = JSON.parse(trimmed);
          this._broadcast(wsClients, data);
          if (data.type === 'complete' && onComplete) {
            onComplete(data);
          }
        } catch (e) {
          // Not JSON, ignore
        }
      }
    });

    this._process.stderr.on('data', (chunk) => {
      // Python stderr — log to console but don't crash
      console.error('[Python]', chunk.toString().trim());
    });

    this._process.on('close', (code) => {
      this._isTraining = false;
      this._process = null;
      if (code !== 0) {
        this._broadcast(wsClients, {
          type: 'error',
          message: `Training process exited with code ${code}`,
        });
      }
    });

    this._process.on('error', (err) => {
      this._isTraining = false;
      this._process = null;
      this._broadcast(wsClients, {
        type: 'error',
        message: `Failed to start Python: ${err.message}. Make sure Python is in PATH.`,
      });
    });

    return { success: true, message: 'Training started' };
  }

  stopTraining() {
    if (this._process) {
      this._process.kill();
      this._process = null;
      this._isTraining = false;
      return { success: true, message: 'Training stopped' };
    }
    return { success: false, message: 'No training in progress' };
  }

  _broadcast(wsClients, data) {
    const msg = JSON.stringify({
      type: data.type === 'progress' ? 'training_progress'
           : data.type === 'complete' ? 'training_complete'
           : 'training_error',
      data,
    });
    for (const client of wsClients) {
      try {
        if (client.readyState === 1 /* OPEN */) {
          client.send(msg);
        }
      } catch (e) {
        // client disconnected
      }
    }
  }
}

module.exports = { TrainingManager };
