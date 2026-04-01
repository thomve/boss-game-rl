import { Component, OnInit, OnDestroy } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WebsocketService } from './services/websocket.service';

@Component({
    selector: 'app-root',
    imports: [RouterOutlet],
    template: `<router-outlet />`,
    styles: [`
    :host { display: block; min-height: 100vh; }
  `]
})
export class AppComponent implements OnInit, OnDestroy {
  constructor(private ws: WebsocketService) {}

  ngOnInit() {
    this.ws.connect();
  }

  ngOnDestroy() {
    this.ws.disconnect();
  }
}
