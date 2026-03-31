"""
Training Script
================
Trains the DQN agent against the boss and outputs metrics.
"""

import sys
import json
import numpy as np
from environment import BossFightEnv
from agent import DQNAgent


def train(n_episodes: int = 800, print_every: int = 50):
    env = BossFightEnv()
    agent = DQNAgent(
        state_size=env.n_observations,
        action_size=env.n_actions,
        hidden_sizes=[256, 128],
        lr=0.0008,
        gamma=0.97,
        epsilon_start=1.0,
        epsilon_end=0.05,
        epsilon_decay=0.9993,
        buffer_size=30000,
        batch_size=128,
        target_update_freq=30,
    )

    # Tracking
    all_rewards = []
    all_wins = []
    all_lengths = []
    metrics_history = []
    rolling_window = 100

    for episode in range(1, n_episodes + 1):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            mask = env.get_action_mask()
            action = agent.choose_action(state, mask)
            next_state, reward, done, info = env.step(action)
            next_mask = env.get_action_mask()
            agent.store_transition(state, action, reward, next_state, done, next_mask)
            loss = agent.train()
            state = next_state
            total_reward += reward

        agent.decay_epsilon()
        all_rewards.append(total_reward)
        all_wins.append(1 if info.get("winner") == "player" else 0)
        all_lengths.append(info.get("turns", 0))

        if episode % print_every == 0:
            recent_rewards = all_rewards[-rolling_window:]
            recent_wins = all_wins[-rolling_window:]
            recent_lengths = all_lengths[-rolling_window:]

            avg_reward = np.mean(recent_rewards)
            win_rate = np.mean(recent_wins) * 100
            avg_length = np.mean(recent_lengths)

            metrics = {
                "episode": episode,
                "avg_reward": round(float(avg_reward), 2),
                "win_rate": round(float(win_rate), 1),
                "avg_length": round(float(avg_length), 1),
                "epsilon": round(float(agent.epsilon), 4),
            }
            metrics_history.append(metrics)
            print(
                f"Ep {episode:5d} | "
                f"Avg Reward: {avg_reward:7.2f} | "
                f"Win Rate: {win_rate:5.1f}% | "
                f"Avg Turns: {avg_length:5.1f} | "
                f"Epsilon: {agent.epsilon:.4f}",
                file=sys.stderr,
            )

    # Save agent
    agent.save("trained_agent.json")

    # Run evaluation games
    agent.epsilon = 0.0  # Pure exploitation
    eval_games = []
    n_eval = 20
    eval_wins = 0
    for _ in range(n_eval):
        state = env.reset()
        done = False
        game_log = []
        while not done:
            mask = env.get_action_mask()
            q_vals = agent.get_q_values(state)
            action = agent.choose_action(state, mask)
            render = env.render()
            render["q_values"] = q_vals.tolist()
            render["action_taken"] = int(action)
            render["action_name"] = env.game.player.abilities[action].name
            game_log.append(render)
            state, _, done, info = env.step(action)
        if info.get("winner") == "player":
            eval_wins += 1
        final = env.render()
        final["q_values"] = [0] * env.n_actions
        final["action_taken"] = -1
        final["action_name"] = "---"
        game_log.append(final)
        eval_games.append(game_log)

    # Output everything as JSON
    output = {
        "training_metrics": metrics_history,
        "eval_win_rate": round(eval_wins / n_eval * 100, 1),
        "eval_games": eval_games[:5],  # Include 5 sample games
        "abilities": {
            "player": [
                {"name": a.name, "description": a.description}
                for a in env.game.player.abilities
            ],
            "boss": [
                {"name": a.name, "description": a.description}
                for a in env.game.boss.abilities
            ],
        },
    }
    print(json.dumps(output))


if __name__ == "__main__":
    train()