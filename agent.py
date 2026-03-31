"""
DQN Agent for Boss Fight
=========================
Deep Q-Network with experience replay, target network,
action masking, and epsilon-greedy exploration.
"""

import random
import numpy as np
from collections import deque


class NeuralNetwork:
    """
    Simple feedforward neural network using only NumPy.
    Architecture: input -> hidden1 (ReLU) -> hidden2 (ReLU) -> output
    """

    def __init__(self, input_size: int, hidden_sizes: list, output_size: int, lr: float = 0.001):
        self.lr = lr
        self.layers = []
        self.biases = []

        sizes = [input_size] + hidden_sizes + [output_size]
        for i in range(len(sizes) - 1):
            # He initialization
            w = np.random.randn(sizes[i], sizes[i + 1]) * np.sqrt(2.0 / sizes[i])
            b = np.zeros((1, sizes[i + 1]))
            self.layers.append(w)
            self.biases.append(b)

    def forward(self, x: np.ndarray) -> tuple:
        """Forward pass, returns (output, cache for backprop)."""
        cache = [x]
        a = x
        for i, (w, b) in enumerate(zip(self.layers, self.biases)):
            z = a @ w + b
            if i < len(self.layers) - 1:  # ReLU for hidden layers
                a = np.maximum(0, z)
            else:
                a = z  # Linear output for Q-values
            cache.append(a)
        return a, cache

    def predict(self, x: np.ndarray) -> np.ndarray:
        output, _ = self.forward(x)
        return output

    def train_step(self, x: np.ndarray, targets: np.ndarray, action_indices: np.ndarray):
        """
        One gradient descent step.
        Only updates Q-values for the taken actions.
        """
        batch_size = x.shape[0]
        output, cache = self.forward(x)

        # Compute loss gradient only for selected actions
        d_output = np.zeros_like(output)
        for i in range(batch_size):
            a = action_indices[i]
            d_output[i, a] = 2 * (output[i, a] - targets[i]) / batch_size

        # Backpropagation
        d_a = d_output
        grads_w = []
        grads_b = []

        for i in reversed(range(len(self.layers))):
            if i < len(self.layers) - 1:
                # ReLU derivative
                d_a = d_a * (cache[i + 1] > 0).astype(float)

            d_w = cache[i].T @ d_a
            d_b = np.sum(d_a, axis=0, keepdims=True)

            # Gradient clipping
            d_w = np.clip(d_w, -1.0, 1.0)
            d_b = np.clip(d_b, -1.0, 1.0)

            grads_w.insert(0, d_w)
            grads_b.insert(0, d_b)

            if i > 0:
                d_a = d_a @ self.layers[i].T

        # Update weights
        for i in range(len(self.layers)):
            self.layers[i] -= self.lr * grads_w[i]
            self.biases[i] -= self.lr * grads_b[i]

        # Return loss
        loss = 0
        for i in range(batch_size):
            a = action_indices[i]
            loss += (output[i, a] - targets[i]) ** 2
        return loss / batch_size

    def copy_weights_from(self, other: "NeuralNetwork"):
        """Copy weights from another network (for target network update)."""
        for i in range(len(self.layers)):
            self.layers[i] = other.layers[i].copy()
            self.biases[i] = other.biases[i].copy()


class DQNAgent:
    """
    Deep Q-Network agent with:
    - Experience replay buffer
    - Target network (soft update)
    - Epsilon-greedy exploration with decay
    - Action masking for valid abilities
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

        # Networks
        self.q_network = NeuralNetwork(state_size, hidden_sizes, action_size, lr)
        self.target_network = NeuralNetwork(state_size, hidden_sizes, action_size, lr)
        self.target_network.copy_weights_from(self.q_network)

        # Experience replay
        self.memory = deque(maxlen=buffer_size)
        self.train_steps = 0

    def choose_action(self, state: np.ndarray, action_mask: np.ndarray) -> int:
        """Epsilon-greedy action selection with masking."""
        valid_actions = np.where(action_mask > 0)[0]
        if len(valid_actions) == 0:
            return 0  # Fallback

        if random.random() < self.epsilon:
            return random.choice(valid_actions)

        q_values = self.q_network.predict(state.reshape(1, -1))[0]
        # Mask invalid actions with -inf
        masked_q = q_values.copy()
        masked_q[action_mask == 0] = -np.inf
        return int(np.argmax(masked_q))

    def store_transition(self, state, action, reward, next_state, done, action_mask):
        self.memory.append((state, action, reward, next_state, done, action_mask))

    def train(self) -> float:
        """Sample from replay buffer and perform one training step."""
        if len(self.memory) < self.batch_size:
            return 0.0

        batch = random.sample(self.memory, self.batch_size)
        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])
        next_masks = np.array([t[5] for t in batch])

        # Compute targets using target network
        next_q = self.target_network.predict(next_states)
        # Mask invalid actions in next state
        next_q[next_masks == 0] = -np.inf
        max_next_q = np.max(next_q, axis=1)
        # Handle case where all actions are masked
        max_next_q = np.where(np.isinf(max_next_q), 0, max_next_q)

        targets = rewards + self.gamma * max_next_q * (1 - dones)

        loss = self.q_network.train_step(states, targets, actions)

        self.train_steps += 1
        if self.train_steps % self.target_update_freq == 0:
            self.target_network.copy_weights_from(self.q_network)

        return loss

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        """Get Q-values for visualization."""
        return self.q_network.predict(state.reshape(1, -1))[0]

    def save(self, filepath: str):
        """Save agent weights."""
        data = {
            "q_layers": [l.tolist() for l in self.q_network.layers],
            "q_biases": [b.tolist() for b in self.q_network.biases],
            "epsilon": self.epsilon,
            "train_steps": self.train_steps,
        }
        import json
        with open(filepath, "w") as f:
            json.dump(data, f)

    def load(self, filepath: str):
        """Load agent weights."""
        import json
        with open(filepath, "r") as f:
            data = json.load(f)
        for i, (l, b) in enumerate(zip(data["q_layers"], data["q_biases"])):
            self.q_network.layers[i] = np.array(l)
            self.q_network.biases[i] = np.array(b)
        self.target_network.copy_weights_from(self.q_network)
        self.epsilon = data["epsilon"]
        self.train_steps = data["train_steps"]