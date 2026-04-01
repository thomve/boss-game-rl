import { Component, OnInit, OnDestroy } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { GameService } from '../services/game.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterLink, CommonModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent implements OnInit, OnDestroy {
  hasAgent = false;
  particles: { x: number; delay: number; duration: number }[] = [];
  private _sub!: Subscription;

  constructor(private gameService: GameService) {
    // Generate background floating particles
    this.particles = Array.from({ length: 30 }, () => ({
      x: Math.random() * 100,
      delay: -(Math.random() * 12),
      duration: 8 + Math.random() * 10,
    }));
  }

  ngOnInit(): void {
    this._sub = this.gameService.hasAgent$.subscribe(v => this.hasAgent = v);
  }

  ngOnDestroy(): void {
    this._sub?.unsubscribe();
  }
}
