'use strict';

const path = require('path');
const fs   = require('fs');
const { BossFightGame, DuelGame } = require('./engine');
const { DQNAgent } = require('./agent');

const WEIGHTS_PATH = path.resolve(__dirname, '../../../trained_agent.json');

class GameManager {
  constructor() {
    this.mode     = 'watch'; // 'watch' | 'play' | 'duel'
    this.bossType = 'dragon'; // 'dragon' | 'witch'
    this.game     = new BossFightGame(this.bossType);
    this.agent    = new DQNAgent();
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
    const valid = ['watch', 'play', 'duel'];
    if (!valid.includes(mode)) return;
    this.mode = mode;
    // Switching to/from duel requires a different game instance
    if (mode === 'duel' && !(this.game instanceof DuelGame)) {
      this.game = new DuelGame();
    } else if (mode !== 'duel' && this.game instanceof DuelGame) {
      this.game = new BossFightGame(this.bossType);
    }
  }

  setBoss(bossType) {
    const valid = ['dragon', 'witch'];
    if (!valid.includes(bossType)) return this._buildResponse();
    this.bossType = bossType;
    // Only applies in non-duel mode
    if (!(this.game instanceof DuelGame)) {
      this.game = new BossFightGame(this.bossType);
    }
    return this._buildResponse();
  }

  reset() {
    this.game = this.mode === 'duel' ? new DuelGame() : new BossFightGame(this.bossType);
    return this._buildResponse();
  }

  /**
   * Human player performs an action (play mode or duel mode).
   * In duel mode the agent responds automatically in the same step.
   */
  playerAction(actionIndex) {
    if (this.game.done) return this._buildResponse();

    if (this.mode === 'duel' && this.game instanceof DuelGame) {
      // Compute agent's response before stepping so both use pre-action state awareness
      const agentState = this.game.getAgentState();
      const agentMask  = this.game.getAgentActionMask();
      const agentAction = this.agent.isLoaded()
        ? this.agent.chooseAction(agentState, agentMask)
        : 0; // fallback: Strike
      this.game.step(actionIndex, agentAction);
    } else {
      this.game.step(actionIndex);
    }

    return this._buildResponse();
  }

  /**
   * Agent performs one step (watch mode only).
   */
  agentStep() {
    if (this.game.done || !this.agent.isLoaded()) return this._buildResponse();
    const state  = this.game.getState();
    const mask   = this.game.getActionMask();
    const action = this.agent.chooseAction(state, mask);
    this.game.step(action);
    return this._buildResponse();
  }

  _buildResponse() {
    const render  = this.game.render();
    const state   = this.game.getState();
    const isDuel  = this.mode === 'duel';
    // Show Q-values in watch mode; hide in duel (agent is opaque to player)
    const qValues = (!isDuel && this.agent.isLoaded()) ? this.agent.getQValues(state) : null;
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
      bossType: this.bossType,
      turn: this.game.turn,
      done: this.game.done,
      winner: this.game.winner,
    };
  }
}

module.exports = { GameManager };
