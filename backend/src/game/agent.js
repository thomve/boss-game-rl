'use strict';

const fs = require('fs');

/**
 * Pure JavaScript inference agent.
 * Supports standard DQN/Double-DQN/PER-DQN networks and Dueling DQN.
 * Handles all four activation functions: relu, leaky_relu, tanh, sigmoid.
 * No training — forward pass only.
 */
class DQNAgent {
  constructor() {
    this.loaded = false;
    this._type = 'standard';   // 'standard' | 'dueling'
    this._activation = 'relu';

    // Standard network
    this.weights = null;
    this.biases  = null;

    // Dueling network
    this._sharedWeights = null;
    this._sharedBiases  = null;
    this._valueW = null;
    this._valueB = null;
    this._advW   = null;
    this._advB   = null;
  }

  // ── Activation ────────────────────────────────────────────────────────────

  _activate(vec) {
    switch (this._activation) {
      case 'leaky_relu': return vec.map(v => v > 0 ? v : 0.01 * v);
      case 'tanh':       return vec.map(v => Math.tanh(v));
      case 'sigmoid':    return vec.map(v => 1 / (1 + Math.exp(-Math.max(-500, Math.min(500, v)))));
      default:           return vec.map(v => Math.max(0, v));  // relu
    }
  }

  // ── Matrix math ───────────────────────────────────────────────────────────

  _matMul(a, b) {
    const rows = a.length, cols = b[0].length, inner = b.length;
    const result = Array.from({ length: rows }, () => new Array(cols).fill(0));
    for (let i = 0; i < rows; i++)
      for (let k = 0; k < inner; k++) {
        if (a[i][k] === 0) continue;
        for (let j = 0; j < cols; j++) result[i][j] += a[i][k] * b[k][j];
      }
    return result;
  }

  _addBias(z, bias) {
    for (let r = 0; r < z.length; r++)
      for (let c = 0; c < z[r].length; c++) z[r][c] += bias[0][c];
    return z;
  }

  // ── Forward passes ────────────────────────────────────────────────────────

  _forwardStandard(state) {
    let a = [state];
    for (let i = 0; i < this.weights.length; i++) {
      const z = this._addBias(this._matMul(a, this.weights[i]), this.biases[i]);
      a = i < this.weights.length - 1 ? z.map(row => this._activate(row)) : z;
    }
    return a[0];
  }

  _forwardDueling(state) {
    // Shared trunk
    let a = [state];
    for (let i = 0; i < this._sharedWeights.length; i++) {
      const z = this._addBias(this._matMul(a, this._sharedWeights[i]), this._sharedBiases[i]);
      a = z.map(row => this._activate(row));
    }

    const h = a;  // (1 × last_hidden)

    // Value head → scalar
    const V = this._addBias(this._matMul(h, this._valueW), this._valueB)[0][0];

    // Advantage head → (n_actions,)
    const A = this._addBias(this._matMul(h, this._advW), this._advB)[0];
    const meanA = A.reduce((s, v) => s + v, 0) / A.length;

    return A.map(a_i => V + a_i - meanA);
  }

  forward(state) {
    if (!this.loaded) return [0, 0, 0, 0, 0];
    return this._type === 'dueling'
      ? this._forwardDueling(state)
      : this._forwardStandard(state);
  }

  // ── Action selection ──────────────────────────────────────────────────────

  getQValues(state) { return this.forward(state); }

  chooseAction(state, mask) {
    const qValues = this.forward(state);
    let bestAction = -1, bestQ = -Infinity;
    for (let i = 0; i < qValues.length; i++) {
      if (mask[i] === 1 && qValues[i] > bestQ) { bestQ = qValues[i]; bestAction = i; }
    }
    if (bestAction === -1) {
      for (let i = 0; i < mask.length; i++) if (mask[i] === 1) return i;
      return 0;
    }
    return bestAction;
  }

  // ── Load weights ──────────────────────────────────────────────────────────

  /**
   * Load weights from a JSON file saved by the Python agent.
   * Handles both 'standard' and 'dueling' formats.
   */
  loadWeights(filepath) {
    try {
      const data = JSON.parse(fs.readFileSync(filepath, 'utf8'));

      this._activation = data.activation || 'relu';
      this._type = data.type === 'dueling' ? 'dueling' : 'standard';

      if (this._type === 'dueling') {
        this._sharedWeights = data.q_shared_layers;
        this._sharedBiases  = data.q_shared_biases;
        this._valueW = data.q_value_w;
        this._valueB = data.q_value_b;
        this._advW   = data.q_adv_w;
        this._advB   = data.q_adv_b;
      } else {
        this.weights = data.q_layers;
        this.biases  = data.q_biases;
      }

      this.loaded = true;
      return true;
    } catch (err) {
      this.loaded = false;
      return false;
    }
  }

  isLoaded() { return this.loaded; }
}

module.exports = { DQNAgent };
