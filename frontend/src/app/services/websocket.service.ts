import { Injectable, OnDestroy } from '@angular/core';
import { Subject, Observable } from 'rxjs';

export interface WsMessage {
  type: string;
  [key: string]: unknown;
}

@Injectable({ providedIn: 'root' })
export class WebsocketService implements OnDestroy {
  private ws: WebSocket | null = null;
  private readonly WS_URL = 'ws://localhost:3000';
  private reconnectDelay = 2000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  private _messages$ = new Subject<WsMessage>();
  readonly messages$: Observable<WsMessage> = this._messages$.asObservable();

  connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    this.intentionalClose = false;
    this._open();
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  private _open(): void {
    try {
      this.ws = new WebSocket(this.WS_URL);

      this.ws.onopen = () => {
        console.log('[WS] Connected');
        this.reconnectDelay = 2000;
      };

      this.ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data) as WsMessage;
          this._messages$.next(msg);
        } catch {
          // ignore malformed
        }
      };

      this.ws.onclose = () => {
        if (!this.intentionalClose) {
          console.log(`[WS] Disconnected — reconnecting in ${this.reconnectDelay}ms`);
          this.reconnectTimer = setTimeout(() => this._open(), this.reconnectDelay);
          this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 15000);
        }
      };

      this.ws.onerror = () => {
        // Let onclose handle reconnect
      };
    } catch (err) {
      console.error('[WS] Failed to connect:', err);
    }
  }

  send(msg: WsMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  // ─── Convenience methods ─────────────────────────────────────────────────
  sendAction(action: number): void {
    this.send({ type: 'game_action', action });
  }

  resetGame(): void {
    this.send({ type: 'game_reset' });
  }

  setMode(mode: 'watch' | 'play'): void {
    this.send({ type: 'game_mode', mode });
  }

  triggerAgentStep(): void {
    this.send({ type: 'agent_step' });
  }

  startTraining(episodes: number, modelConfig?: { hiddenLayers: number; neuronsPerLayer: number; activation: string; algorithm: string }): void {
    this.send({ type: 'start_training', episodes, ...modelConfig });
  }

  stopTraining(): void {
    this.send({ type: 'stop_training' });
  }

  requestAgentStatus(): void {
    this.send({ type: 'agent_status' });
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}
