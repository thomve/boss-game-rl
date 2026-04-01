'use strict';

const path = require('path');
const fs = require('fs');
const { BossFightGame } = require('./engine');
const { DQNAgent } = require('./agent');

const WEIGHTS_PATH = path.resolve(__dirname, '../../../trained_agent.json');

class GameManager {
  constructor() {
    this.game = new BossFightGame();
    this.agent = new DQNAgent();
    this.mode = 'watch'; // 'watch' | 'play'
    this.autoPlay = false;
    this._tryLoadAgent();
  }

  _tryLoadAgent() {
    if (fs.existsSync(WEIGHTS_PATH)) {
      this.agent.loadWeights(WEIGHTS_PATH);
    }
  }

  reloadAgent() {
    this._tryLoadAgent();
    return this.agent.isLoaded();
  }

  hasAgent() {
    return this.agent.isLoaded();
  }

  setMode(mode) {
    this.mode = mode;
  }

  reset() {
    this.game.reset();
    return this._buildResponse();
  }

  /**
   * Human player performs an action.
   */
  playerAction(actionIndex) {
    if (this.game.done) {
      return this._buildResponse();
    }
    this.game.step(actionIndex);
    return this._buildResponse();
  }

  /**
   * Agent performs one step (watch mode).
   */
  agentStep() {
    if (this.game.done || !this.agent.isLoaded()) {
      return this._buildResponse();
    }
    const state = this.game.getState();
    const mask = this.game.getActionMask();
    const action = this.agent.chooseAction(state, mask);
    this.game.step(action);
    return this._buildResponse();
  }

  _buildResponse() {
    const render = this.game.render();
    const state = this.game.getState();
    const qValues = this.agent.isLoaded() ? this.agent.getQValues(state) : null;
    return {
      ...render,
      qValues,
      hasAgent: this.agent.isLoaded(),
      mode: this.mode,
    };
  }

  getStatus() {
    return {
      hasAgent: this.agent.isLoaded(),
      mode: this.mode,
      turn: this.game.turn,
      done: this.game.done,
      winner: this.game.winner,
    };
  }
}

module.exports = { GameManager };
