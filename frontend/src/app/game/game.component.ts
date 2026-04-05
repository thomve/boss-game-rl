import { Component, OnInit, OnDestroy } from '@angular/core';

import { ActivatedRoute, RouterLink } from '@angular/router';
import { Subscription, interval } from 'rxjs';
import { takeWhile } from 'rxjs/operators';
import { WebsocketService } from '../services/websocket.service';
import { GameService, GameState, FighterState } from '../services/game.service';
import { FighterPanelComponent } from './components/fighter-panel/fighter-panel.component';
import { CombatLogComponent } from './components/combat-log/combat-log.component';
import { QChartComponent } from './components/q-chart/q-chart.component';

@Component({
    selector: 'app-game',
    imports: [
    RouterLink,
    FighterPanelComponent,
    CombatLogComponent,
    QChartComponent
],
    templateUrl: './game.component.html',
    styleUrls: ['./game.component.scss']
})
export class GameComponent implements OnInit, OnDestroy {
  state: GameState | null = null;
  mode: 'watch' | 'play' | 'duel' = 'watch';
  autoPlay = false;
  autoPlaySpeed = 800; // ms between steps
  isThinking = false;

  private _subs: Subscription[] = [];
  private _autoPlaySub: Subscription | null = null;

  constructor(
    private ws: WebsocketService,
    private gameService: GameService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const queryMode = this.route.snapshot.queryParamMap.get('mode');
    if (queryMode === 'play') {
      this.mode = 'play';
    } else if (queryMode === 'duel') {
      this.mode = 'duel';
    } else {
      this.mode = 'watch';
    }
    this.ws.setMode(this.mode);

    this._subs.push(
      this.gameService.state$.subscribe(s => {
        this.state = s;
        this.isThinking = false;
      })
    );

    this.ws.resetGame();
  }

  ngOnDestroy(): void {
    this._subs.forEach(s => s.unsubscribe());
    this._stopAutoPlay();
  }

  setMode(m: 'watch' | 'play' | 'duel'): void {
    this.mode = m;
    this.ws.setMode(m);
    if (m !== 'watch') this._stopAutoPlay();
  }

  doAction(i: number): void {
    if (this.state?.done) return;
    if (this.mode === 'play' || this.mode === 'duel') {
      this.ws.sendAction(i);
    }
  }

  agentStep(): void {
    if (this.state?.done || !this.state?.hasAgent) return;
    this.isThinking = true;
    this.ws.triggerAgentStep();
  }

  resetGame(): void {
    this._stopAutoPlay();
    this.autoPlay = false;
    this.ws.resetGame();
  }

  toggleAutoPlay(): void {
    this.autoPlay = !this.autoPlay;
    if (this.autoPlay) {
      this._startAutoPlay();
    } else {
      this._stopAutoPlay();
    }
  }

  private _startAutoPlay(): void {
    this._stopAutoPlay();
    this._autoPlaySub = interval(this.autoPlaySpeed)
      .pipe(takeWhile(() => this.autoPlay && !this.state?.done))
      .subscribe(() => {
        if (!this.state?.done && this.state?.hasAgent) {
          this.isThinking = true;
          this.ws.triggerAgentStep();
        } else if (this.state?.done) {
          this._stopAutoPlay();
          this.autoPlay = false;
        }
      });
  }

  private _stopAutoPlay(): void {
    this._autoPlaySub?.unsubscribe();
    this._autoPlaySub = null;
  }

  setSpeed(ms: number): void {
    this.autoPlaySpeed = ms;
    if (this.autoPlay) {
      this._startAutoPlay();
    }
  }

  getActionMask(): number[] {
    return this.state?.player?.abilities?.map(a => a.available ? 1 : 0) ?? [1,1,1,1,1];
  }

  getTurnProgress(): number {
    if (!this.state) return 0;
    return (this.state.turn / this.state.maxTurns) * 100;
  }

  getAgentAsFighter(): FighterState {
    return this.state!.boss as unknown as FighterState;
  }
}
