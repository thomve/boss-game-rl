"""
Gym-compatible Environment Wrapper
===================================
Wraps the BossFightGame for use with RL algorithms.
"""

import random
import numpy as np
from game_engine import BossFightGame

BOSS_TYPES = ['dragon', 'witch']


class BossFightEnv:
    """
    OpenAI Gym-like environment for the boss fight.
    Observation: 20-dimensional float vector (normalized 0-1)
    Action space: 5 discrete actions (player abilities)

    boss_type: 'dragon', 'witch', or None (random each episode).
    """

    def __init__(self, boss_type: str = None):
        self.boss_type = boss_type  # None → random per episode
        initial_boss = boss_type or 'dragon'
        self.game = BossFightGame(initial_boss)
        self.n_actions = 5
        self.n_observations = len(self.game.get_state())

    def reset(self) -> np.ndarray:
        if self.boss_type is None:
            # Alternate randomly between bosses so agent learns both
            chosen = random.choice(BOSS_TYPES)
            self.game = BossFightGame(chosen)
        state = self.game.reset()
        return self._state_to_array(state)

    def step(self, action: int) -> tuple:
        state, reward, done, info = self.game.step(action)
        return self._state_to_array(state), reward, done, info

    def get_action_mask(self) -> np.ndarray:
        return np.array(self.game.get_action_mask(), dtype=np.float32)

    def _state_to_array(self, state: dict) -> np.ndarray:
        return np.array(list(state.values()), dtype=np.float32)

    def get_valid_actions(self) -> list:
        return self.game.get_valid_actions()

    def render(self) -> dict:
        """Return current state for visualization."""
        g = self.game
        return {
            "turn": g.turn,
            "player": {
                "name": g.player.name,
                "hp": g.player.hp,
                "max_hp": g.player.max_hp,
                "mana": g.player.mana,
                "max_mana": g.player.max_mana,
                "effects": [
                    {"name": e.effect.value, "duration": e.duration}
                    for e in g.player.active_effects
                ],
                "abilities": [
                    {
                        "name": a.name,
                        "cooldown": a.current_cooldown,
                        "max_cooldown": a.cooldown,
                        "mana_cost": a.mana_cost,
                        "available": a.is_available(g.player.mana),
                    }
                    for a in g.player.abilities
                ],
            },
            "boss": {
                "name": g.boss.name,
                "hp": g.boss.hp,
                "max_hp": g.boss.max_hp,
                "mana": g.boss.mana,
                "max_mana": g.boss.max_mana,
                "effects": [
                    {"name": e.effect.value, "duration": e.duration}
                    for e in g.boss.active_effects
                ],
            },
            "done": g.done,
            "winner": g.winner,
        }