import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Subscription } from 'rxjs';
import { WebsocketService } from './websocket.service';

export interface TrainingMetric {
  episode: number;
  avgReward: number;
  winRate: number;
  avgTurns: number;
  epsilon: number;
}

@Injectable({ providedIn: 'root' })
export class TrainingService implements OnDestroy {
  private _isTraining$ = new BehaviorSubject<boolean>(false);
  private _metrics$ = new BehaviorSubject<TrainingMetric[]>([]);
  private _latestMetric$ = new BehaviorSubject<TrainingMetric | null>(null);
  private _status$ = new BehaviorSubject<string>('idle');
  private _sub!: Subscription;

  readonly isTraining$ = this._isTraining$.asObservable();
  readonly metrics$ = this._metrics$.asObservable();
  readonly latestMetric$ = this._latestMetric$.asObservable();
  readonly status$ = this._status$.asObservable();

  constructor(private ws: WebsocketService) {
    this._sub = this.ws.messages$.subscribe(msg => {
      switch (msg['type']) {
        case 'training_started':
          this._isTraining$.next(true);
          this._status$.next('training');
          this._metrics$.next([]);
          break;

        case 'training_progress': {
          const d = msg['data'] as {
            episode: number; total: number; avg_reward: number;
            win_rate: number; avg_turns: number; epsilon: number;
          };
          const metric: TrainingMetric = {
            episode: d.episode,
            avgReward: d.avg_reward,
            winRate: d.win_rate,
            avgTurns: d.avg_turns,
            epsilon: d.epsilon,
          };
          const current = this._metrics$.getValue();
          this._metrics$.next([...current, metric]);
          this._latestMetric$.next(metric);
          break;
        }

        case 'training_complete':
          this._isTraining$.next(false);
          this._status$.next('complete');
          break;

        case 'training_stopped':
          this._isTraining$.next(false);
          this._status$.next('idle');
          break;

        case 'training_error':
          this._isTraining$.next(false);
          this._status$.next('error');
          break;
      }
    });
  }

  clearMetrics(): void {
    this._metrics$.next([]);
    this._latestMetric$.next(null);
    this._status$.next('idle');
  }

  ngOnDestroy(): void {
    this._sub.unsubscribe();
  }
}
