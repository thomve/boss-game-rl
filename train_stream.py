"""
Training Stream Script
======================
Modified training script that outputs JSON lines to stdout
so Node.js can read and stream metrics in real-time.
"""

import sys
import json
import argparse
from collections import deque

# Allow running from any directory
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from environment import BossFightEnv
from agent import DQNAgent


def train(episodes: int = 800, output_path: str = "trained_agent.json"):
    try:
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

        rewards_window = deque(maxlen=100)
        wins_window = deque(maxlen=100)
        turns_window = deque(maxlen=100)

        for episode in range(1, episodes + 1):
            state = env.reset()
            total_reward = 0
            done = False

            while not done:
                mask = env.get_action_mask()
                action = agent.choose_action(state, mask)
                next_state, reward, done, info = env.step(action)
                next_mask = env.get_action_mask()
                agent.store_transition(state, action, reward, next_state, done, next_mask)
                agent.train()
                state = next_state
                total_reward += reward

            agent.decay_epsilon()
            rewards_window.append(total_reward)
            wins_window.append(1 if info.get('winner') == 'player' else 0)
            turns_window.append(info.get('turns', 0))

            if episode % 10 == 0:
                avg_reward = float(sum(rewards_window) / len(rewards_window))
                win_rate = float(sum(wins_window) / len(wins_window))
                avg_turns = float(sum(turns_window) / len(turns_window))

                print(json.dumps({
                    "type": "progress",
                    "episode": episode,
                    "total": episodes,
                    "avg_reward": round(avg_reward, 2),
                    "win_rate": round(win_rate, 3),
                    "avg_turns": round(avg_turns, 1),
                    "epsilon": round(float(agent.epsilon), 4)
                }), flush=True)

        # Save weights
        agent.save(output_path)

        # Final win rate from last window
        final_win_rate = float(sum(wins_window) / len(wins_window)) if wins_window else 0.0

        print(json.dumps({
            "type": "complete",
            "win_rate": round(final_win_rate, 3),
            "weights_saved": True
        }), flush=True)

    except Exception as e:
        print(json.dumps({
            "type": "error",
            "message": str(e)
        }), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train DQN agent with streaming output")
    parser.add_argument("--episodes", type=int, default=800, help="Number of training episodes")
    parser.add_argument("--output", type=str, default="trained_agent.json", help="Output path for weights")
    args = parser.parse_args()

    train(episodes=args.episodes, output_path=args.output)
