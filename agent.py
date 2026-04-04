"""
DQN Agent for Boss Fight
=========================
Supports four RL algorithms:
  - dqn:         Vanilla Deep Q-Network
  - double_dqn:  Double DQN (reduces overestimation bias)
  - dueling_dqn: Dueling DQN (separate value + advantage streams)
  - per_dqn:     DQN with Prioritized Experience Replay
"""

import json
import random
import numpy as np
from collections import deque


ACTIVATIONS = ('relu', 'tanh', 'sigmoid', 'leaky_relu')
ALGORITHMS  = ('dqn', 'double_dqn', 'dueling_dqn', 'per_dqn')


# ─── Activation helpers ───────────────────────────────────────────────────────

def _activate(z: np.ndarray, name: str) -> np.ndarray:
    if name == 'relu':
        return np.maximum(0, z)
    elif name == 'leaky_relu':
        return np.where(z > 0, z, 0.01 * z)
    elif name == 'tanh':
        return np.tanh(z)
    elif name == 'sigmoid':
        return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))
    return np.maximum(0, z)


def _activate_grad(a: np.ndarray, name: str) -> np.ndarray:
    """Derivative of activation given post-activation values."""
    if name == 'relu':
        return (a > 0).astype(float)
    elif name == 'leaky_relu':
        return np.where(a > 0, 1.0, 0.01)
    elif name == 'tanh':
        return 1.0 - a ** 2
    elif name == 'sigmoid':
        return a * (1.0 - a)
    return (a > 0).astype(float)


def _init_weight(fan_in: int, fan_out: int, activation: str) -> np.ndarray:
    """He init for relu/leaky_relu, Xavier for tanh/sigmoid."""
    if activation in ('relu', 'leaky_relu'):
        return np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)
    return np.random.randn(fan_in, fan_out) * np.sqrt(1.0 / fan_in)


# ─── Standard feedforward network ─────────────────────────────────────────────

class NeuralNetwork:
    """Fully-connected network: input → hidden (activation) → output (linear)."""

    def __init__(self, input_size: int, hidden_sizes: list, output_size: int,
                 lr: float = 0.001, activation: str = 'relu'):
        self.lr = lr
        self.activation = activation if activation in ACTIVATIONS else 'relu'
        self.layers = []
        self.biases = []

        for fan_in, fan_out in zip(
            [input_size] + hidden_sizes,
            hidden_sizes + [output_size],
        ):
            self.layers.append(_init_weight(fan_in, fan_out, self.activation))
            self.biases.append(np.zeros((1, fan_out)))

    def forward(self, x: np.ndarray) -> tuple:
        cache = [x]
        a = x
        for i, (w, b) in enumerate(zip(self.layers, self.biases)):
            z = a @ w + b
            a = _activate(z, self.activation) if i < len(self.layers) - 1 else z
            cache.append(a)
        return a, cache

    def predict(self, x: np.ndarray) -> np.ndarray:
        out, _ = self.forward(x)
        return out

    def train_step(self, x: np.ndarray, targets: np.ndarray,
                   action_indices: np.ndarray, weights: np.ndarray = None) -> tuple:
        """
        One gradient descent step.  Only updates Q-values for taken actions.
        Returns (mean_loss, per_sample_td_errors).
        """
        batch_size = x.shape[0]
        output, cache = self.forward(x)

        td_errors = np.array([output[i, action_indices[i]] - targets[i]
                               for i in range(batch_size)])

        d_output = np.zeros_like(output)
        for i in range(batch_size):
            a = action_indices[i]
            w_i = float(weights[i]) if weights is not None else 1.0
            d_output[i, a] = 2.0 * td_errors[i] * w_i / batch_size

        d_a = d_output
        grads_w, grads_b = [], []

        for i in reversed(range(len(self.layers))):
            if i < len(self.layers) - 1:
                d_a = d_a * _activate_grad(cache[i + 1], self.activation)
            d_w = np.clip(cache[i].T @ d_a, -1.0, 1.0)
            d_b = np.clip(np.sum(d_a, axis=0, keepdims=True), -1.0, 1.0)
            grads_w.insert(0, d_w)
            grads_b.insert(0, d_b)
            if i > 0:
                d_a = d_a @ self.layers[i].T

        for i in range(len(self.layers)):
            self.layers[i] -= self.lr * grads_w[i]
            self.biases[i] -= self.lr * grads_b[i]

        return float(np.mean(td_errors ** 2)), td_errors

    def copy_weights_from(self, other: "NeuralNetwork"):
        for i in range(len(self.layers)):
            self.layers[i] = other.layers[i].copy()
            self.biases[i] = other.biases[i].copy()


# ─── Dueling network ──────────────────────────────────────────────────────────

class DuelingNeuralNetwork:
    """
    Dueling architecture: shared trunk → Value stream V(s) + Advantage stream A(s,a).
    Q(s,a) = V(s) + A(s,a) - mean_a(A(s,a))
    """

    def __init__(self, input_size: int, hidden_sizes: list, output_size: int,
                 lr: float = 0.001, activation: str = 'relu'):
        self.lr = lr
        self.activation = activation if activation in ACTIVATIONS else 'relu'
        self.output_size = output_size

        self.shared_layers: list = []
        self.shared_biases: list = []

        last = input_size
        for h in hidden_sizes:
            self.shared_layers.append(_init_weight(last, h, self.activation))
            self.shared_biases.append(np.zeros((1, h)))
            last = h

        # Value head: last_hidden → 1
        self.value_w = _init_weight(last, 1, self.activation)
        self.value_b = np.zeros((1, 1))

        # Advantage head: last_hidden → n_actions
        self.adv_w = _init_weight(last, output_size, self.activation)
        self.adv_b = np.zeros((1, output_size))

    def forward(self, x: np.ndarray) -> tuple:
        """Returns (Q, shared_cache, h)."""
        cache = [x]
        a = x
        for w, b in zip(self.shared_layers, self.shared_biases):
            a = _activate(a @ w + b, self.activation)
            cache.append(a)

        h = a
        V = h @ self.value_w + self.value_b          # (batch, 1)
        A = h @ self.adv_w   + self.adv_b            # (batch, n_actions)
        Q = V + A - A.mean(axis=1, keepdims=True)    # (batch, n_actions)
        return Q, cache, h

    def predict(self, x: np.ndarray) -> np.ndarray:
        Q, _, _ = self.forward(x)
        return Q

    def train_step(self, x: np.ndarray, targets: np.ndarray,
                   action_indices: np.ndarray, weights: np.ndarray = None) -> tuple:
        batch_size = x.shape[0]
        Q, cache, h = self.forward(x)

        td_errors = np.array([Q[i, action_indices[i]] - targets[i]
                               for i in range(batch_size)])

        dQ = np.zeros_like(Q)
        for i in range(batch_size):
            w_i = float(weights[i]) if weights is not None else 1.0
            dQ[i, action_indices[i]] = 2.0 * td_errors[i] * w_i / batch_size

        # Gradients to V and A from the dueling combination
        dV = dQ.sum(axis=1, keepdims=True)                    # (batch, 1)
        dA = dQ - dQ.mean(axis=1, keepdims=True)              # (batch, n_actions)

        dV_w = np.clip(h.T @ dV, -1.0, 1.0)
        dV_b = np.clip(dV.sum(axis=0, keepdims=True), -1.0, 1.0)
        dA_w = np.clip(h.T @ dA, -1.0, 1.0)
        dA_b = np.clip(dA.sum(axis=0, keepdims=True), -1.0, 1.0)

        # Gradient flowing back into shared trunk
        d_a = dV @ self.value_w.T + dA @ self.adv_w.T

        grads_w, grads_b = [], []
        for i in reversed(range(len(self.shared_layers))):
            d_a = d_a * _activate_grad(cache[i + 1], self.activation)
            grads_w.insert(0, np.clip(cache[i].T @ d_a, -1.0, 1.0))
            grads_b.insert(0, np.clip(d_a.sum(axis=0, keepdims=True), -1.0, 1.0))
            if i > 0:
                d_a = d_a @ self.shared_layers[i].T

        for i in range(len(self.shared_layers)):
            self.shared_layers[i] -= self.lr * grads_w[i]
            self.shared_biases[i] -= self.lr * grads_b[i]

        self.value_w -= self.lr * dV_w
        self.value_b -= self.lr * dV_b
        self.adv_w   -= self.lr * dA_w
        self.adv_b   -= self.lr * dA_b

        return float(np.mean(td_errors ** 2)), td_errors

    def copy_weights_from(self, other: "DuelingNeuralNetwork"):
        for i in range(len(self.shared_layers)):
            self.shared_layers[i] = other.shared_layers[i].copy()
            self.shared_biases[i] = other.shared_biases[i].copy()
        self.value_w = other.value_w.copy()
        self.value_b = other.value_b.copy()
        self.adv_w   = other.adv_w.copy()
        self.adv_b   = other.adv_b.copy()


# ─── Prioritized Experience Replay buffer ─────────────────────────────────────

class PrioritizedReplayBuffer:
    """Replay buffer that samples transitions proportional to |TD error|^alpha."""

    def __init__(self, maxlen: int, alpha: float = 0.6):
        self.maxlen = maxlen
        self.alpha = alpha
        self._buffer: list = []
        self._priorities: list = []
        self._pos = 0

    def add(self, transition, priority: float = 1.0):
        p = (abs(priority) + 1e-6) ** self.alpha
        if len(self._buffer) < self.maxlen:
            self._buffer.append(transition)
            self._priorities.append(p)
        else:
            self._buffer[self._pos] = transition
            self._priorities[self._pos] = p
        self._pos = (self._pos + 1) % self.maxlen

    def sample(self, batch_size: int, beta: float = 0.4) -> tuple:
        n = len(self._buffer)
        probs = np.array(self._priorities[:n], dtype=np.float64)
        probs /= probs.sum()

        indices = np.random.choice(n, size=batch_size,
                                   p=probs, replace=(n < batch_size))
        weights = (n * probs[indices]) ** (-beta)
        weights = (weights / weights.max()).astype(np.float32)

        return [self._buffer[i] for i in indices], weights, indices

    def update_priorities(self, indices, td_errors):
        for idx, err in zip(indices, td_errors):
            self._priorities[idx] = (abs(float(err)) + 1e-6) ** self.alpha

    def __len__(self):
        return len(self._buffer)


# ─── DQN Agent ────────────────────────────────────────────────────────────────

class DQNAgent:
    """
    Unified agent supporting DQN, Double DQN, Dueling DQN, and PER-DQN.

    algorithm choices:
      'dqn'         – Vanilla DQN
      'double_dqn'  – Double DQN (online net selects action, target net evaluates)
      'dueling_dqn' – Dueling network architecture (V + A streams)
      'per_dqn'     – Prioritized Experience Replay DQN
    """

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_sizes: list = None,
        lr: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: float = 0.998,
        buffer_size: int = 10000,
        batch_size: int = 64,
        target_update_freq: int = 20,
        activation: str = 'relu',
        algorithm: str = 'dqn',
    ):
        if hidden_sizes is None:
            hidden_sizes = [128, 64]

        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.algorithm = algorithm if algorithm in ALGORITHMS else 'dqn'

        # Build networks
        NetworkClass = DuelingNeuralNetwork if self.algorithm == 'dueling_dqn' else NeuralNetwork
        self.q_network      = NetworkClass(state_size, hidden_sizes, action_size, lr, activation)
        self.target_network = NetworkClass(state_size, hidden_sizes, action_size, lr, activation)
        self.target_network.copy_weights_from(self.q_network)

        # Experience replay buffer
        if self.algorithm == 'per_dqn':
            self.memory = PrioritizedReplayBuffer(maxlen=buffer_size)
            self._beta = 0.4
            self._beta_increment = 0.0001
        else:
            self.memory = deque(maxlen=buffer_size)

        self.train_steps = 0

    # ── Action selection ───────────────────────────────────────────────────

    def choose_action(self, state: np.ndarray, action_mask: np.ndarray) -> int:
        valid_actions = np.where(action_mask > 0)[0]
        if len(valid_actions) == 0:
            return 0

        if random.random() < self.epsilon:
            return int(random.choice(valid_actions))

        q_values = self.q_network.predict(state.reshape(1, -1))[0]
        masked_q = q_values.copy()
        masked_q[action_mask == 0] = -np.inf
        return int(np.argmax(masked_q))

    # ── Memory storage ─────────────────────────────────────────────────────

    def store_transition(self, state, action, reward, next_state, done, action_mask):
        transition = (state, action, reward, next_state, done, action_mask)
        if self.algorithm == 'per_dqn':
            # New transitions get the current max priority so they are sampled once
            max_p = max(self.memory._priorities[:len(self.memory)]) if len(self.memory) > 0 else 1.0
            self.memory.add(transition, priority=max_p)
        else:
            self.memory.append(transition)

    # ── Training step ──────────────────────────────────────────────────────

    def train(self) -> float:
        if len(self.memory) < self.batch_size:
            return 0.0

        # Sample batch
        if self.algorithm == 'per_dqn':
            batch, is_weights, sample_indices = self.memory.sample(self.batch_size, self._beta)
            self._beta = min(1.0, self._beta + self._beta_increment)
        else:
            batch = random.sample(list(self.memory), self.batch_size)
            is_weights = None
            sample_indices = None

        states      = np.array([t[0] for t in batch])
        actions     = np.array([t[1] for t in batch])
        rewards     = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones       = np.array([t[4] for t in batch])
        next_masks  = np.array([t[5] for t in batch])

        # Compute bootstrap targets
        if self.algorithm == 'double_dqn':
            # Online net picks the action, target net evaluates it
            next_q_online = self.q_network.predict(next_states).copy()
            next_q_online[next_masks == 0] = -np.inf
            best_actions = np.argmax(next_q_online, axis=1)
            next_q_target = self.target_network.predict(next_states)
            max_next_q = next_q_target[np.arange(len(batch)), best_actions]
        else:
            next_q = self.target_network.predict(next_states)
            next_q[next_masks == 0] = -np.inf
            max_next_q = np.max(next_q, axis=1)

        max_next_q = np.where(np.isinf(max_next_q), 0.0, max_next_q)
        targets = rewards + self.gamma * max_next_q * (1 - dones)

        loss, td_errors = self.q_network.train_step(states, targets, actions, is_weights)

        if self.algorithm == 'per_dqn' and sample_indices is not None:
            self.memory.update_priorities(sample_indices, td_errors)

        self.train_steps += 1
        if self.train_steps % self.target_update_freq == 0:
            self.target_network.copy_weights_from(self.q_network)

        return loss

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        return self.q_network.predict(state.reshape(1, -1))[0]

    # ── Persistence ────────────────────────────────────────────────────────

    def save(self, filepath: str):
        if self.algorithm == 'dueling_dqn':
            net = self.q_network
            data = {
                "type": "dueling",
                "activation": net.activation,
                "q_shared_layers": [l.tolist() for l in net.shared_layers],
                "q_shared_biases": [b.tolist() for b in net.shared_biases],
                "q_value_w": net.value_w.tolist(),
                "q_value_b": net.value_b.tolist(),
                "q_adv_w":   net.adv_w.tolist(),
                "q_adv_b":   net.adv_b.tolist(),
                "epsilon": self.epsilon,
                "train_steps": self.train_steps,
            }
        else:
            net = self.q_network
            data = {
                "type": "standard",
                "activation": net.activation,
                "q_layers":  [l.tolist() for l in net.layers],
                "q_biases":  [b.tolist() for b in net.biases],
                "epsilon": self.epsilon,
                "train_steps": self.train_steps,
            }
        with open(filepath, "w") as f:
            json.dump(data, f)

    def load(self, filepath: str):
        with open(filepath, "r") as f:
            data = json.load(f)

        model_type = data.get("type", "standard")
        if model_type == "dueling" and isinstance(self.q_network, DuelingNeuralNetwork):
            net = self.q_network
            for i, (l, b) in enumerate(zip(data["q_shared_layers"], data["q_shared_biases"])):
                net.shared_layers[i] = np.array(l)
                net.shared_biases[i] = np.array(b)
            net.value_w = np.array(data["q_value_w"])
            net.value_b = np.array(data["q_value_b"])
            net.adv_w   = np.array(data["q_adv_w"])
            net.adv_b   = np.array(data["q_adv_b"])
        else:
            for i, (l, b) in enumerate(zip(data["q_layers"], data["q_biases"])):
                self.q_network.layers[i] = np.array(l)
                self.q_network.biases[i] = np.array(b)

        self.target_network.copy_weights_from(self.q_network)
        self.epsilon     = data.get("epsilon", self.epsilon_end)
        self.train_steps = data.get("train_steps", 0)
