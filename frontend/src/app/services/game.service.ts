import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Subscription } from 'rxjs';
import { WebsocketService } from './websocket.service';

export interface AbilityState {
  name: string;
  damage: number;
  heal: number;
  manaCost: number;
  cooldown: number;
  currentCooldown: number;
  available: boolean;
  description: string;
}

export interface EffectState {
  name: string;
  duration: number;
  potency: number;
}

export interface FighterState {
  name: string;
  hp: number;
  maxHp: number;
  mana: number;
  maxMana: number;
  effects: EffectState[];
  abilities: AbilityState[];
}

export interface BossState {
  name: string;
  hp: number;
  maxHp: number;
  mana: number;
  maxMana: number;
  effects: EffectState[];
  // Full ability info in duel mode; minimal info in boss mode
  abilities: AbilityState[];
}

export interface GameState {
  turn: number;
  maxTurns: number;
  done: boolean;
  winner: string | null;
  log: string[];
  player: FighterState;
  boss: BossState;
  qValues: number[] | null;
  hasAgent: boolean;
  isDuel: boolean;
  mode: 'watch' | 'play' | 'duel';
  bossType: 'dragon' | 'witch';
}

@Injectable({ providedIn: 'root' })
export class GameService implements OnDestroy {
  private _state$ = new BehaviorSubject<GameState | null>(null);
  private _hasAgent$ = new BehaviorSubject<boolean>(false);
  private _sub!: Subscription;

  readonly state$ = this._state$.asObservable();
  readonly hasAgent$ = this._hasAgent$.asObservable();

  constructor(private ws: WebsocketService) {
    this._sub = this.ws.messages$.subscribe(msg => {
      if (msg['type'] === 'game_state') {
        this._state$.next(msg['state'] as GameState);
      }
      if (msg['type'] === 'agent_status') {
        this._hasAgent$.next(msg['hasAgent'] as boolean);
      }
    });
  }

  getState(): GameState | null {
    return this._state$.getValue();
  }

  isWatchMode(): boolean {
    return this._state$.getValue()?.mode === 'watch';
  }

  isPlayMode(): boolean {
    return this._state$.getValue()?.mode === 'play';
  }

  isDuelMode(): boolean {
    return this._state$.getValue()?.mode === 'duel';
  }

  ngOnDestroy(): void {
    this._sub.unsubscribe();
  }
}
