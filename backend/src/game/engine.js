'use strict';

// ─── Status Effect Constants ───────────────────────────────────────────────
const StatusEffect = {
  POISON: 'poison',
  SHIELD: 'shield',
  STUNNED: 'stunned',
  REGEN: 'regen',
  ENRAGED: 'enraged',
  WEAKENED: 'weakened',
};

// ─── Ability ───────────────────────────────────────────────────────────────
class Ability {
  constructor(name, damage, heal, cooldown, manaCost, appliesEffect, description) {
    this.name = name;
    this.damage = damage;
    this.heal = heal;
    this.cooldown = cooldown;
    this.currentCooldown = 0;
    this.manaCost = manaCost || 0;
    this.appliesEffect = appliesEffect || null; // [effectType, duration, potency]
    this.description = description || '';
  }

  isAvailable(mana) {
    return this.currentCooldown === 0 && mana >= this.manaCost;
  }

  use() {
    this.currentCooldown = this.cooldown;
  }

  tickCooldown() {
    if (this.currentCooldown > 0) {
      this.currentCooldown -= 1;
    }
  }
}

// ─── Active Effect ─────────────────────────────────────────────────────────
class ActiveEffect {
  constructor(effect, duration, potency) {
    this.effect = effect;
    this.duration = duration;
    this.potency = potency;
  }
}

// ─── Fighter ───────────────────────────────────────────────────────────────
class Fighter {
  constructor(name, maxHp, maxMana, manaRegen, abilities) {
    this.name = name;
    this.maxHp = maxHp;
    this.hp = maxHp;
    this.maxMana = maxMana;
    this.mana = maxMana;
    this.manaRegen = manaRegen;
    this.abilities = abilities;
    this.activeEffects = [];
  }

  isAlive() {
    return this.hp > 0;
  }

  applyDamage(amount) {
    const shield = this.activeEffects.find(e => e.effect === StatusEffect.SHIELD);
    if (shield) {
      const reduced = amount * (1 - shield.potency);
      this.hp = Math.max(0, this.hp - reduced);
    } else {
      this.hp = Math.max(0, this.hp - amount);
    }
  }

  applyHeal(amount) {
    this.hp = Math.min(this.maxHp, this.hp + amount);
  }

  applyManaRegen() {
    this.mana = Math.min(this.maxMana, this.mana + this.manaRegen);
  }

  hasEffect(effectType) {
    return this.activeEffects.some(e => e.effect === effectType);
  }

  addEffect(effectType, duration, potency) {
    // Replace existing effect of same type
    this.activeEffects = this.activeEffects.filter(e => e.effect !== effectType);
    this.activeEffects.push(new ActiveEffect(effectType, duration, potency));
  }

  /**
   * Process active effects. Returns array of log strings.
   */
  tickEffects() {
    const logs = [];
    for (const eff of this.activeEffects) {
      if (eff.effect === StatusEffect.POISON) {
        this.hp = Math.max(0, this.hp - eff.potency);
        logs.push(`  ${this.name} takes ${Math.round(eff.potency)} poison damage`);
      } else if (eff.effect === StatusEffect.REGEN) {
        this.applyHeal(eff.potency);
        logs.push(`  ${this.name} regenerates ${Math.round(eff.potency)} HP`);
      }
      eff.duration -= 1;
    }
    this.activeEffects = this.activeEffects.filter(e => e.duration > 0);
    return logs;
  }

  tickCooldowns() {
    for (const ability of this.abilities) {
      ability.tickCooldown();
    }
  }
}

// ─── Factory Functions ──────────────────────────────────────────────────────
function createHero() {
  return new Fighter('Hero', 120, 60, 8, [
    new Ability('Strike', 15, 0, 0, 0, null, 'Basic attack dealing 15 damage'),
    new Ability('Power Slash', 30, 0, 2, 12, null, 'Heavy strike dealing 30 damage'),
    new Ability('Heal', 0, 30, 3, 10, null, 'Restore 30 HP'),
    new Ability('Poison Blade', 10, 0, 3, 8,
      [StatusEffect.POISON, 3, 6],
      'Deal 10 damage and apply 6 poison for 3 turns'),
    new Ability('Shield Up', 0, 0, 4, 8,
      [StatusEffect.SHIELD, 2, 0.5],
      'Reduce incoming damage by 50% for 2 turns'),
  ]);
}

function createDragon() {
  return new Fighter('Dragon Lord', 180, 60, 6, [
    new Ability('Claw Swipe', 10, 0, 0, 0, null, 'Basic claw attack'),
    new Ability('Fire Breath', 25, 0, 3, 18, null, 'Devastating fire attack'),
    new Ability('Tail Slam', 15, 0, 2, 10,
      [StatusEffect.STUNNED, 1, 0],
      'Heavy slam that stuns for 1 turn'),
    new Ability('Dark Heal', 0, 20, 5, 15, null, 'Regenerate 20 HP'),
    new Ability('Enrage', 0, 0, 6, 12,
      [StatusEffect.ENRAGED, 3, 1.4],
      'Increase damage by 40% for 3 turns'),
  ]);
}

// ─── BossFightGame ─────────────────────────────────────────────────────────
class BossFightGame {
  constructor() {
    this.MAX_TURNS = 50;
    this.reset();
  }

  reset() {
    this.hero = createHero();
    this.dragon = createDragon();
    this.turn = 0;
    this.done = false;
    this.winner = null;
    this.log = [];
    return this.getState();
  }

  getState() {
    const h = this.hero;
    const b = this.dragon;
    return [
      h.hp / h.maxHp,
      h.mana / h.maxMana,
      b.hp / b.maxHp,
      b.mana / b.maxMana,
      this.turn / this.MAX_TURNS,
      // Player ability cooldowns (normalized)
      ...h.abilities.map(a => a.currentCooldown / Math.max(a.cooldown, 1)),
      // Boss ability cooldowns (normalized)
      ...b.abilities.map(a => a.currentCooldown / Math.max(a.cooldown, 1)),
      // Status effects (binary)
      h.hasEffect(StatusEffect.POISON) ? 1 : 0,
      h.hasEffect(StatusEffect.SHIELD) ? 1 : 0,
      h.hasEffect(StatusEffect.STUNNED) ? 1 : 0,
      h.hasEffect(StatusEffect.REGEN) ? 1 : 0,
      b.hasEffect(StatusEffect.POISON) ? 1 : 0,
      b.hasEffect(StatusEffect.ENRAGED) ? 1 : 0,
    ];
  }

  getValidActions() {
    if (this.hero.hasEffect(StatusEffect.STUNNED)) return [];
    return this.hero.abilities
      .map((a, i) => a.isAvailable(this.hero.mana) ? i : -1)
      .filter(i => i >= 0);
  }

  getActionMask() {
    if (this.hero.hasEffect(StatusEffect.STUNNED)) {
      return [0, 0, 0, 0, 0];
    }
    return this.hero.abilities.map(a => a.isAvailable(this.hero.mana) ? 1 : 0);
  }

  _bossAI() {
    if (this.dragon.hasEffect(StatusEffect.STUNNED)) return -1;

    const available = this.dragon.abilities
      .map((a, i) => a.isAvailable(this.dragon.mana) ? i : -1)
      .filter(i => i >= 0);

    if (available.length === 0) return 0;

    // Heal if low HP
    if (this.dragon.hp < this.dragon.maxHp * 0.3 && available.includes(3)) {
      return 3; // Dark Heal
    }

    // Enrage if available and not already enraged
    if (available.includes(4) && !this.dragon.hasEffect(StatusEffect.ENRAGED)) {
      if (Math.random() < 0.4) return 4;
    }

    // Fire Breath
    if (available.includes(1) && Math.random() < 0.6) return 1;

    // Tail Slam
    if (available.includes(2) && Math.random() < 0.5) return 2;

    // Random fallback
    return available[Math.floor(Math.random() * available.length)];
  }

  _executeAbility(user, target, ability) {
    const logs = [`  ${user.name} uses ${ability.name}!`];
    user.mana -= ability.manaCost;

    let damage = ability.damage;

    // Enrage buff
    if (user.hasEffect(StatusEffect.ENRAGED) && damage > 0) {
      const enrage = user.activeEffects.find(e => e.effect === StatusEffect.ENRAGED);
      damage *= enrage.potency;
      logs.push(`  ENRAGED! Damage boosted to ${Math.round(damage)}`);
    }

    // Weakened debuff
    if (target.hasEffect(StatusEffect.WEAKENED) && damage > 0) {
      damage *= 1.3;
    }

    if (damage > 0) {
      target.applyDamage(damage);
      logs.push(`  ${target.name} takes ${Math.round(damage)} damage (${Math.round(target.hp)} HP remaining)`);
    }

    if (ability.heal > 0) {
      user.applyHeal(ability.heal);
      logs.push(`  ${user.name} heals for ${ability.heal} (${Math.round(user.hp)} HP)`);
    }

    if (ability.appliesEffect) {
      const [effect, duration, potency] = ability.appliesEffect;
      const selfEffects = [StatusEffect.SHIELD, StatusEffect.ENRAGED, StatusEffect.REGEN];
      if (selfEffects.includes(effect)) {
        user.addEffect(effect, duration, potency);
        logs.push(`  ${user.name} gains ${effect} for ${duration} turns`);
      } else {
        target.addEffect(effect, duration, potency);
        logs.push(`  ${target.name} is afflicted with ${effect} for ${duration} turns`);
      }
    }

    ability.use();
    return logs;
  }

  step(playerAction) {
    this.turn += 1;
    const turnLog = [`\n=== Turn ${this.turn} ===`];
    let reward = 0;

    // ── Player Phase ────────────────────────────────────────────────────────
    if (this.hero.hasEffect(StatusEffect.STUNNED)) {
      turnLog.push(`  ${this.hero.name} is STUNNED and cannot act!`);
    } else {
      const valid = this.getValidActions();
      let action = playerAction;
      if (!valid.includes(action)) action = valid.length > 0 ? valid[0] : 0;

      const ability = this.hero.abilities[action];
      const logs = this._executeAbility(this.hero, this.dragon, ability);
      turnLog.push(...logs);

      reward += (ability.damage / this.dragon.maxHp) * 2.0;
      if (ability.appliesEffect && ability.appliesEffect[0] === StatusEffect.POISON) {
        reward += 0.3;
      }
    }

    // Check boss death
    if (!this.dragon.isAlive()) {
      this.done = true;
      this.winner = 'player';
      reward += 10.0;
      turnLog.push(`\n  *** ${this.dragon.name} has been DEFEATED! ***`);
      this.log.push(...turnLog);
      return { state: this.getState(), reward, done: true, info: { winner: 'player', turn: this.turn } };
    }

    // ── Boss Phase ──────────────────────────────────────────────────────────
    const bossAction = this._bossAI();
    if (bossAction === -1) {
      turnLog.push(`  ${this.dragon.name} is STUNNED and cannot act!`);
    } else {
      const ability = this.dragon.abilities[bossAction];
      const prevHp = this.hero.hp;
      const logs = this._executeAbility(this.dragon, this.hero, ability);
      turnLog.push(...logs);
      const damageTaken = prevHp - this.hero.hp;
      reward -= (damageTaken / this.hero.maxHp) * 1.5;
    }

    // Check player death
    if (!this.hero.isAlive()) {
      this.done = true;
      this.winner = 'boss';
      reward -= 5.0;
      turnLog.push(`\n  *** ${this.hero.name} has been DEFEATED! ***`);
      this.log.push(...turnLog);
      return { state: this.getState(), reward, done: true, info: { winner: 'boss', turn: this.turn } };
    }

    // ── End of Turn ─────────────────────────────────────────────────────────
    turnLog.push('  -- Effects --');
    turnLog.push(...this.hero.tickEffects());
    turnLog.push(...this.dragon.tickEffects());

    if (!this.dragon.isAlive()) {
      this.done = true;
      this.winner = 'player';
      reward += 10.0;
      turnLog.push(`\n  *** ${this.dragon.name} succumbs to effects! ***`);
    } else if (!this.hero.isAlive()) {
      this.done = true;
      this.winner = 'boss';
      reward -= 5.0;
      turnLog.push(`\n  *** ${this.hero.name} succumbs to effects! ***`);
    }

    this.hero.tickCooldowns();
    this.dragon.tickCooldowns();
    this.hero.applyManaRegen();
    this.dragon.applyManaRegen();

    const hpRatio = this.hero.hp / this.hero.maxHp;
    const bossHpRatio = this.dragon.hp / this.dragon.maxHp;
    reward += (hpRatio - bossHpRatio) * 0.1;

    if (this.hero.hp < this.hero.maxHp * 0.25) {
      reward -= 0.2;
    }

    if (this.turn >= this.MAX_TURNS && !this.done) {
      this.done = true;
      this.winner = 'boss';
      reward -= 3.0;
      turnLog.push("\n  *** Time's up! The Hero retreats... ***");
    }

    this.log.push(...turnLog);

    return {
      state: this.getState(),
      reward,
      done: this.done,
      info: {
        winner: this.winner,
        turn: this.turn,
        playerHp: this.hero.hp,
        bossHp: this.dragon.hp,
      },
    };
  }

  render() {
    return {
      turn: this.turn,
      maxTurns: this.MAX_TURNS,
      done: this.done,
      winner: this.winner,
      log: this.log.slice(-30), // last 30 lines
      player: {
        name: this.hero.name,
        hp: Math.round(this.hero.hp),
        maxHp: this.hero.maxHp,
        mana: Math.round(this.hero.mana),
        maxMana: this.hero.maxMana,
        effects: this.hero.activeEffects.map(e => ({ name: e.effect, duration: e.duration, potency: e.potency })),
        abilities: this.hero.abilities.map(a => ({
          name: a.name,
          damage: a.damage,
          heal: a.heal,
          manaCost: a.manaCost,
          cooldown: a.cooldown,
          currentCooldown: a.currentCooldown,
          available: a.isAvailable(this.hero.mana),
          description: a.description,
        })),
      },
      boss: {
        name: this.dragon.name,
        hp: Math.round(this.dragon.hp),
        maxHp: this.dragon.maxHp,
        mana: Math.round(this.dragon.mana),
        maxMana: this.dragon.maxMana,
        effects: this.dragon.activeEffects.map(e => ({ name: e.effect, duration: e.duration, potency: e.potency })),
        abilities: this.dragon.abilities.map(a => ({
          name: a.name,
          currentCooldown: a.currentCooldown,
          available: a.isAvailable(this.dragon.mana),
        })),
      },
    };
  }
}

module.exports = { BossFightGame, createHero, createDragon, StatusEffect, Ability, Fighter };
