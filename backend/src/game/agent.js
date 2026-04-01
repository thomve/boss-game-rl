'use strict';

const fs = require('fs');
const path = require('path');

/**
 * Pure JavaScript DQN inference agent.
 * Architecture: Input(20) -> ReLU(256) -> ReLU(128) -> Linear(5)
 * No training in Node.js — only forward pass / inference.
 */
class DQNAgent {
  constructor() {
    this.weights = null; // Array of weight matrices
    this.biases = null;  // Array of bias vectors
    this.loaded = false;
  }

  /**
   * Matrix multiplication: (m x n) @ (n x p) -> (m x p)
   */
  _matMul(a, b) {
    const rows = a.length;
    const cols = b[0].length;
    const inner = b.length;
    const result = Array.from({ length: rows }, () => new Array(cols).fill(0));
    for (let i = 0; i < rows; i++) {
      for (let k = 0; k < inner; k++) {
        if (a[i][k] === 0) continue;
        for (let j = 0; j < cols; j++) {
          result[i][j] += a[i][k] * b[k][j];
        }
      }
    }
    return result;
  }

  /**
   * ReLU activation applied element-wise to a row vector.
   */
  _relu(vec) {
    return vec.map(v => Math.max(0, v));
  }

  /**
   * Forward pass through the network.
   * @param {number[]} state - 20-element state array
   * @returns {number[]} 5-element Q-value array
   */
  forward(state) {
    if (!this.loaded) return [0, 0, 0, 0, 0];

    // Input: [1 x 20]
    let a = [state];

    for (let i = 0; i < this.weights.length; i++) {
      // z = a @ W + b
      const z = this._matMul(a, this.weights[i]);
      // Add bias
      for (let r = 0; r < z.length; r++) {
        for (let c = 0; c < z[r].length; c++) {
          z[r][c] += this.biases[i][0][c];
        }
      }
      // ReLU on hidden layers, linear on output
      if (i < this.weights.length - 1) {
        a = z.map(row => this._relu(row));
      } else {
        a = z;
      }
    }

    return a[0]; // [Q0, Q1, Q2, Q3, Q4]
  }

  /**
   * Get Q-values for a state.
   */
  getQValues(state) {
    return this.forward(state);
  }

  /**
   * Choose the best valid action.
   * @param {number[]} state
   * @param {number[]} mask - binary array [0|1] for each action
   * @returns {number} action index
   */
  chooseAction(state, mask) {
    const qValues = this.forward(state);
    let bestAction = -1;
    let bestQ = -Infinity;

    for (let i = 0; i < qValues.length; i++) {
      if (mask[i] === 1 && qValues[i] > bestQ) {
        bestQ = qValues[i];
        bestAction = i;
      }
    }

    // Fallback: first valid action
    if (bestAction === -1) {
      for (let i = 0; i < mask.length; i++) {
        if (mask[i] === 1) return i;
      }
      return 0;
    }

    return bestAction;
  }

  /**
   * Load weights from a JSON file saved by the Python agent.
   * Expected format: { q_layers: [[...]], q_biases: [[...]], epsilon, train_steps }
   */
  loadWeights(filepath) {
    try {
      const data = JSON.parse(fs.readFileSync(filepath, 'utf8'));

      // q_layers[i] is shape [in x out] stored as nested arrays
      this.weights = data.q_layers;
      this.biases = data.q_biases;
      this.loaded = true;
      return true;
    } catch (err) {
      this.loaded = false;
      return false;
    }
  }

  isLoaded() {
    return this.loaded;
  }
}

module.exports = { DQNAgent };
