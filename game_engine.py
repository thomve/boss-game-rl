"""
Boss Fight Game Engine
======================
A turn-based boss fight with abilities, cooldowns, and status effects.
"""

import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class StatusEffect(Enum):
    POISON = "poison"
    SHIELD = "shield"
    STUNNED = "stunned"
    REGEN = "regen"
    ENRAGED = "enraged"
    WEAKENED = "weakened"


@dataclass
class ActiveEffect:
    effect: StatusEffect
    duration: int  # turns remaining
    potency: float  # damage/heal per tick or modifier


@dataclass
class Ability:
    name: str
    damage: float
    heal: float
    cooldown: int
    current_cooldown: int = 0
    mana_cost: float = 0
    applies_effect: Optional[tuple] = None  # (StatusEffect, duration, potency)
    description: str = ""

    def is_available(self, mana: float) -> bool:
        return self.current_cooldown == 0 and mana >= self.mana_cost

    def use(self):
        self.current_cooldown = self.cooldown

    def tick_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


@dataclass
class Fighter:
    name: str
    max_hp: float
    hp: float
    max_mana: float
    mana: float
    mana_regen: float
    abilities: list = field(default_factory=list)
    active_effects: list = field(default_factory=list)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def apply_damage(self, amount: float):
        # Check for shield
        shield = next((e for e in self.active_effects if e.effect == StatusEffect.SHIELD), None)
        if shield:
            reduced = amount * (1 - shield.potency)
            self.hp = max(0, self.hp - reduced)
        else:
            self.hp = max(0, self.hp - amount)

    def apply_heal(self, amount: float):
        self.hp = min(self.max_hp, self.hp + amount)

    def apply_mana_regen(self):
        self.mana = min(self.max_mana, self.mana + self.mana_regen)

    def has_effect(self, effect: StatusEffect) -> bool:
        return any(e.effect == effect for e in self.active_effects)

    def add_effect(self, effect: StatusEffect, duration: int, potency: float):
        # Replace existing effect of same type
        self.active_effects = [e for e in self.active_effects if e.effect != effect]
        self.active_effects.append(ActiveEffect(effect, duration, potency))

    def tick_effects(self) -> list:
        """Process active effects, return log messages."""
        logs = []
        for eff in self.active_effects:
            if eff.effect == StatusEffect.POISON:
                self.hp = max(0, self.hp - eff.potency)
                logs.append(f"  {self.name} takes {eff.potency:.0f} poison damage")
            elif eff.effect == StatusEffect.REGEN:
                self.apply_heal(eff.potency)
                logs.append(f"  {self.name} regenerates {eff.potency:.0f} HP")
            eff.duration -= 1
        self.active_effects = [e for e in self.active_effects if e.duration > 0]
        return logs

    def tick_cooldowns(self):
        for ability in self.abilities:
            ability.tick_cooldown()


def create_player() -> Fighter:
    """Create the player character."""
    player = Fighter(
        name="Hero",
        max_hp=120,
        hp=120,
        max_mana=60,
        mana=60,
        mana_regen=8,
    )
    player.abilities = [
        Ability(
            name="Strike",
            damage=15,
            heal=0,
            cooldown=0,
            mana_cost=0,
            description="Basic attack dealing 15 damage",
        ),
        Ability(
            name="Power Slash",
            damage=30,
            heal=0,
            cooldown=2,
            mana_cost=12,
            description="Heavy strike dealing 30 damage",
        ),
        Ability(
            name="Heal",
            damage=0,
            heal=30,
            cooldown=3,
            mana_cost=10,
            description="Restore 30 HP",
        ),
        Ability(
            name="Poison Blade",
            damage=10,
            heal=0,
            cooldown=3,
            mana_cost=8,
            applies_effect=(StatusEffect.POISON, 3, 6),
            description="Deal 10 damage and apply 6 poison for 3 turns",
        ),
        Ability(
            name="Shield Up",
            damage=0,
            heal=0,
            cooldown=4,
            mana_cost=8,
            applies_effect=(StatusEffect.SHIELD, 2, 0.5),
            description="Reduce incoming damage by 50% for 2 turns",
        ),
    ]
    return player


def create_dragon() -> Fighter:
    """Create the Dragon Lord boss."""
    boss = Fighter(
        name="Dragon Lord",
        max_hp=180,
        hp=180,
        max_mana=60,
        mana=60,
        mana_regen=6,
    )
    boss.abilities = [
        Ability(
            name="Claw Swipe",
            damage=10,
            heal=0,
            cooldown=0,
            mana_cost=0,
            description="Basic claw attack",
        ),
        Ability(
            name="Fire Breath",
            damage=25,
            heal=0,
            cooldown=3,
            mana_cost=18,
            description="Devastating fire attack",
        ),
        Ability(
            name="Tail Slam",
            damage=15,
            heal=0,
            cooldown=2,
            mana_cost=10,
            applies_effect=(StatusEffect.STUNNED, 1, 0),
            description="Heavy slam that stuns for 1 turn",
        ),
        Ability(
            name="Dark Heal",
            damage=0,
            heal=20,
            cooldown=5,
            mana_cost=15,
            description="Regenerate 20 HP",
        ),
        Ability(
            name="Enrage",
            damage=0,
            heal=0,
            cooldown=6,
            mana_cost=12,
            applies_effect=(StatusEffect.ENRAGED, 3, 1.4),
            description="Increase damage by 40% for 3 turns",
        ),
    ]
    return boss


def create_shadow_witch() -> Fighter:
    """Create the Shadow Witch boss — a fragile spellcaster with sustain and burst."""
    boss = Fighter(
        name="Shadow Witch",
        max_hp=150,
        hp=150,
        max_mana=80,
        mana=80,
        mana_regen=10,
    )
    boss.abilities = [
        Ability(
            name="Shadow Bolt",
            damage=12,
            heal=0,
            cooldown=0,
            mana_cost=0,
            description="Basic dark magic attack",
        ),
        Ability(
            name="Soul Drain",
            damage=18,
            heal=15,
            cooldown=3,
            mana_cost=20,
            description="Drain 18 HP from target and heal self for 15",
        ),
        Ability(
            name="Hex Curse",
            damage=8,
            heal=0,
            cooldown=2,
            mana_cost=12,
            applies_effect=(StatusEffect.WEAKENED, 2, 0),
            description="Deal 8 damage and weaken target for 2 turns",
        ),
        Ability(
            name="Death Coil",
            damage=30,
            heal=0,
            cooldown=4,
            mana_cost=25,
            description="Unleash a devastating dark bolt for 30 damage",
        ),
        Ability(
            name="Phantom Shroud",
            damage=0,
            heal=0,
            cooldown=5,
            mana_cost=18,
            applies_effect=(StatusEffect.SHIELD, 2, 0.5),
            description="Shroud self in shadows, reducing damage by 50% for 2 turns",
        ),
    ]
    return boss


def create_boss(boss_type: str = 'dragon') -> Fighter:
    """Create a boss by type ('dragon' or 'witch')."""
    if boss_type == 'witch':
        return create_shadow_witch()
    return create_dragon()


class BossFightGame:
    """
    Main game controller for the boss fight.
    Manages turns, actions, and game state.
    """

    MAX_TURNS = 50

    def __init__(self, boss_type: str = 'dragon'):
        self.boss_type = boss_type
        self.reset()

    def reset(self):
        self.player = create_player()
        self.boss = create_boss(self.boss_type)
        self.turn = 0
        self.done = False
        self.winner = None
        self.log = []
        return self.get_state()

    def get_state(self) -> dict:
        """Return the current game state as a flat dictionary for RL."""
        state = {
            "player_hp": self.player.hp / self.player.max_hp,
            "player_mana": self.player.mana / self.player.max_mana,
            "boss_hp": self.boss.hp / self.boss.max_hp,
            "boss_mana": self.boss.mana / self.boss.max_mana,
            "turn": self.turn / self.MAX_TURNS,
            # Player ability cooldowns (normalized)
            **{
                f"player_cd_{i}": a.current_cooldown / max(a.cooldown, 1)
                for i, a in enumerate(self.player.abilities)
            },
            # Boss ability cooldowns
            **{
                f"boss_cd_{i}": a.current_cooldown / max(a.cooldown, 1)
                for i, a in enumerate(self.boss.abilities)
            },
            # Status effects (binary)
            "player_poisoned": float(self.player.has_effect(StatusEffect.POISON)),
            "player_shielded": float(self.player.has_effect(StatusEffect.SHIELD)),
            "player_stunned": float(self.player.has_effect(StatusEffect.STUNNED)),
            "player_regen": float(self.player.has_effect(StatusEffect.REGEN)),
            "boss_poisoned": float(self.boss.has_effect(StatusEffect.POISON)),
            "boss_enraged": float(self.boss.has_effect(StatusEffect.ENRAGED)),
        }
        return state

    def get_valid_actions(self) -> list:
        """Return indices of abilities the player can currently use."""
        if self.player.has_effect(StatusEffect.STUNNED):
            return []  # Stunned = skip turn
        return [
            i
            for i, a in enumerate(self.player.abilities)
            if a.is_available(self.player.mana)
        ]

    def get_action_mask(self) -> list:
        """Return a binary mask of valid actions."""
        if self.player.has_effect(StatusEffect.STUNNED):
            return [0] * len(self.player.abilities)
        return [
            1 if a.is_available(self.player.mana) else 0
            for a in self.player.abilities
        ]

    def _boss_choose_action(self) -> int:
        """Route to the appropriate boss AI."""
        if self.boss_type == 'witch':
            return self._shadow_witch_ai()
        return self._dragon_ai()

    def _dragon_ai(self) -> int:
        """Dragon Lord AI with weighted priorities."""
        if self.boss.has_effect(StatusEffect.STUNNED):
            return -1  # Skip

        available = [
            i for i, a in enumerate(self.boss.abilities)
            if a.is_available(self.boss.mana)
        ]
        if not available:
            return 0  # Fallback to basic attack

        # Heal if low HP
        if self.boss.hp < self.boss.max_hp * 0.3 and 3 in available:
            return 3  # Dark Heal

        # Enrage if available and not already enraged
        if 4 in available and not self.boss.has_effect(StatusEffect.ENRAGED):
            if random.random() < 0.4:
                return 4

        # Fire Breath if available
        if 1 in available and random.random() < 0.6:
            return 1

        # Tail Slam
        if 2 in available and random.random() < 0.5:
            return 2

        # Default: random available
        return random.choice(available)

    def _shadow_witch_ai(self) -> int:
        """Shadow Witch AI — sustain, curse, then burst."""
        if self.boss.has_effect(StatusEffect.STUNNED):
            return -1  # Skip

        available = [
            i for i, a in enumerate(self.boss.abilities)
            if a.is_available(self.boss.mana)
        ]
        if not available:
            return 0  # Fallback to Shadow Bolt

        # Soul Drain if low HP (heal + damage)
        if self.boss.hp < self.boss.max_hp * 0.4 and 1 in available:
            return 1  # Soul Drain

        # Phantom Shroud if not already shielded
        if 4 in available and not self.boss.has_effect(StatusEffect.SHIELD):
            if random.random() < 0.35:
                return 4

        # Death Coil high-damage nuke
        if 3 in available and random.random() < 0.65:
            return 3

        # Hex Curse — weaken player
        if 2 in available and not self.player.has_effect(StatusEffect.WEAKENED):
            if random.random() < 0.55:
                return 2

        # Soul Drain for sustain damage
        if 1 in available and random.random() < 0.40:
            return 1

        # Default: random available
        return random.choice(available)

    def _execute_ability(self, user: Fighter, target: Fighter, ability: Ability) -> list:
        """Execute an ability and return log messages."""
        logs = [f"  {user.name} uses {ability.name}!"]
        user.mana -= ability.mana_cost

        damage = ability.damage
        # Check enrage buff
        if user.has_effect(StatusEffect.ENRAGED) and damage > 0:
            enrage = next(e for e in user.active_effects if e.effect == StatusEffect.ENRAGED)
            damage *= enrage.potency
            logs.append(f"  ENRAGED! Damage boosted to {damage:.0f}")

        # Check target weakened
        if target.has_effect(StatusEffect.WEAKENED) and damage > 0:
            damage *= 1.3

        if damage > 0:
            target.apply_damage(damage)
            logs.append(f"  {target.name} takes {damage:.0f} damage ({target.hp:.0f} HP remaining)")

        if ability.heal > 0:
            user.apply_heal(ability.heal)
            logs.append(f"  {user.name} heals for {ability.heal:.0f} ({user.hp:.0f} HP)")

        if ability.applies_effect:
            effect, duration, potency = ability.applies_effect
            if effect in (StatusEffect.SHIELD, StatusEffect.ENRAGED, StatusEffect.REGEN):
                user.add_effect(effect, duration, potency)
                logs.append(f"  {user.name} gains {effect.value} for {duration} turns")
            else:
                target.add_effect(effect, duration, potency)
                logs.append(f"  {target.name} is afflicted with {effect.value} for {duration} turns")

        ability.use()
        return logs

    def step(self, player_action: int) -> tuple:
        """
        Execute one turn of combat.
        Returns: (state, reward, done, info)
        """
        self.turn += 1
        turn_log = [f"\n=== Turn {self.turn} ==="]
        reward = 0

        # --- Player Phase ---
        if self.player.has_effect(StatusEffect.STUNNED):
            turn_log.append(f"  {self.player.name} is STUNNED and cannot act!")
        else:
            valid = self.get_valid_actions()
            if player_action not in valid:
                player_action = 0  # Fallback to basic attack

            ability = self.player.abilities[player_action]
            logs = self._execute_ability(self.player, self.boss, ability)
            turn_log.extend(logs)

            # Reward for dealing damage (proportion of boss HP removed)
            boss_hp_before = self.boss.hp + ability.damage  # approximate
            reward += (ability.damage / self.boss.max_hp) * 2.0
            if ability.applies_effect and ability.applies_effect[0] == StatusEffect.POISON:
                reward += 0.3  # Bonus for applying DoT

        # Check boss death
        if not self.boss.is_alive:
            self.done = True
            self.winner = "player"
            reward += 10.0
            turn_log.append(f"\n  *** {self.boss.name} has been DEFEATED! ***")
            self.log.extend(turn_log)
            return self.get_state(), reward, True, {"winner": "player", "turns": self.turn}

        # --- Boss Phase ---
        boss_action = self._boss_choose_action()
        if boss_action == -1:
            turn_log.append(f"  {self.boss.name} is STUNNED and cannot act!")
        else:
            ability = self.boss.abilities[boss_action]
            prev_hp = self.player.hp
            logs = self._execute_ability(self.boss, self.player, ability)
            turn_log.extend(logs)
            damage_taken = prev_hp - self.player.hp
            reward -= (damage_taken / self.player.max_hp) * 1.5  # Penalty for taking damage

        # Check player death
        if not self.player.is_alive:
            self.done = True
            self.winner = "boss"
            reward -= 5.0
            turn_log.append(f"\n  *** {self.player.name} has been DEFEATED! ***")
            self.log.extend(turn_log)
            return self.get_state(), reward, True, {"winner": "boss", "turns": self.turn}

        # --- End of Turn Maintenance ---
        turn_log.append("  -- Effects --")
        turn_log.extend(self.player.tick_effects())
        turn_log.extend(self.boss.tick_effects())

        # Check deaths from DoT
        if not self.boss.is_alive:
            self.done = True
            self.winner = "player"
            reward += 10.0
            turn_log.append(f"\n  *** {self.boss.name} succumbs to effects! ***")
        elif not self.player.is_alive:
            self.done = True
            self.winner = "boss"
            reward -= 5.0
            turn_log.append(f"\n  *** {self.player.name} succumbs to effects! ***")

        # Cooldowns & mana regen
        self.player.tick_cooldowns()
        self.boss.tick_cooldowns()
        self.player.apply_mana_regen()
        self.boss.apply_mana_regen()

        # Survival reward + HP advantage signal
        hp_ratio = self.player.hp / self.player.max_hp
        boss_hp_ratio = self.boss.hp / self.boss.max_hp
        reward += (hp_ratio - boss_hp_ratio) * 0.1  # Reward for HP advantage

        # Healing reward (incentivize staying alive)
        if self.player.hp < self.player.max_hp * 0.25:
            reward -= 0.2

        # Turn limit
        if self.turn >= self.MAX_TURNS and not self.done:
            self.done = True
            self.winner = "boss"  # Timeout = loss
            reward -= 3.0
            turn_log.append("\n  *** Time's up! The Hero retreats... ***")

        self.log.extend(turn_log)
        info = {
            "winner": self.winner,
            "turns": self.turn,
            "player_hp": self.player.hp,
            "boss_hp": self.boss.hp,
        }
        return self.get_state(), reward, self.done, info


def play_interactive():
    """Play the game interactively in the terminal."""
    game = BossFightGame()
    state = game.reset()

    print("=" * 50)
    print(f"  BOSS FIGHT: Hero vs {game.boss.name}")
    print("=" * 50)

    while not game.done:
        print(f"\n--- Turn {game.turn + 1} ---")
        print(f"  Hero:       {game.player.hp:.0f}/{game.player.max_hp:.0f} HP | {game.player.mana:.0f}/{game.player.max_mana:.0f} MP")
        print(f"  Dragon Lord: {game.boss.hp:.0f}/{game.boss.max_hp:.0f} HP | {game.boss.mana:.0f}/{game.boss.max_mana:.0f} MP")

        effects_p = ", ".join(f"{e.effect.value}({e.duration})" for e in game.player.active_effects)
        effects_b = ", ".join(f"{e.effect.value}({e.duration})" for e in game.boss.active_effects)
        if effects_p:
            print(f"  Hero effects: {effects_p}")
        if effects_b:
            print(f"  Boss effects: {effects_b}")

        valid = game.get_valid_actions()
        print("\n  Available abilities:")
        for i, ability in enumerate(game.player.abilities):
            available = "✓" if i in valid else "✗"
            cd = f" (CD: {ability.current_cooldown})" if ability.current_cooldown > 0 else ""
            mp = f" [{ability.mana_cost} MP]" if ability.mana_cost > 0 else ""
            print(f"    [{available}] {i}: {ability.name}{mp}{cd} - {ability.description}")

        if not valid:
            print("  You are STUNNED! Skipping turn...")
            action = 0
        else:
            while True:
                try:
                    action = int(input("\n  Choose ability (number): "))
                    if action in valid:
                        break
                    print("  Invalid choice!")
                except ValueError:
                    print("  Enter a number!")

        state, reward, done, info = game.step(action)

    # Print combat log
    print("\n" + "=" * 50)
    print("  COMBAT LOG")
    print("=" * 50)
    for line in game.log:
        print(line)


if __name__ == "__main__":
    play_interactive()