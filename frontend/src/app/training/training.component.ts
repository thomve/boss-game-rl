import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import type { Chart as ChartJS } from 'chart.js';
import { WebsocketService } from '../services/websocket.service';
import { TrainingService, TrainingMetric } from '../services/training.service';

@Component({
  selector: 'app-training',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './training.component.html',
  styleUrls: ['./training.component.scss'],
})
export class TrainingComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('rewardCanvas') rewardCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('winCanvas') winCanvas!: ElementRef<HTMLCanvasElement>;

  isTraining = false;
  status = 'idle';
  selectedEpisodes = 800;
  episodeOptions = [100, 200, 500, 800];

  latest: TrainingMetric | null = null;
  metrics: TrainingMetric[] = [];

  private _subs: Subscription[] = [];
  private rewardChart: ChartJS | null = null;
  private winChart: ChartJS | null = null;
  private chartsReady = false;

  constructor(
    private ws: WebsocketService,
    private trainingService: TrainingService,
  ) {}

  ngOnInit(): void {
    this._subs.push(
      this.trainingService.isTraining$.subscribe(v => this.isTraining = v),
      this.trainingService.status$.subscribe(v => this.status = v),
      this.trainingService.latestMetric$.subscribe(v => this.latest = v),
      this.trainingService.metrics$.subscribe(m => {
        this.metrics = m;
        if (this.chartsReady) this._updateCharts();
      }),
    );
  }

  ngAfterViewInit(): void {
    this._initCharts();
  }

  ngOnDestroy(): void {
    this._subs.forEach(s => s.unsubscribe());
  }

  startTraining(): void {
    this.trainingService.clearMetrics();
    this.ws.startTraining(this.selectedEpisodes);
  }

  stopTraining(): void {
    this.ws.stopTraining();
  }

  selectEpisodes(n: number): void {
    this.selectedEpisodes = n;
  }

  getProgress(): number {
    if (!this.latest || !this.selectedEpisodes) return 0;
    return Math.min(100, (this.latest.episode / this.selectedEpisodes) * 100);
  }

  getStatusText(): string {
    switch (this.status) {
      case 'training': return 'Training in progress...';
      case 'complete': return 'Training complete!';
      case 'error': return 'Training error';
      default: return 'Idle';
    }
  }

  getStatusClass(): string {
    switch (this.status) {
      case 'training': return 'status-training';
      case 'complete': return 'status-complete';
      case 'error': return 'status-error';
      default: return 'status-idle';
    }
  }

  private async _initCharts(): Promise<void> {
    const { Chart, LineController, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler } = await import('chart.js');
    Chart.register(LineController, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

    const commonOptions = {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 0 } as const,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { color: '#8888aa', maxTicksLimit: 8, font: { family: 'Rajdhani', size: 10 } as const },
          grid: { color: 'rgba(255,255,255,0.05)' },
        },
        y: {
          ticks: { color: '#8888aa', font: { family: 'Rajdhani', size: 10 } as const },
          grid: { color: 'rgba(255,255,255,0.06)' },
        },
      },
    };

    const rCtx = this.rewardCanvas?.nativeElement?.getContext('2d');
    if (rCtx) {
      this.rewardChart = new Chart(rCtx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Avg Reward',
            data: [],
            borderColor: '#e6c35a',
            backgroundColor: 'rgba(230,195,90,0.1)',
            borderWidth: 2,
            pointRadius: 2,
            fill: true,
            tension: 0.3,
          }],
        },
        options: commonOptions,
      });
    }

    const wCtx = this.winCanvas?.nativeElement?.getContext('2d');
    if (wCtx) {
      this.winChart = new Chart(wCtx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Win Rate',
            data: [],
            borderColor: '#46be50',
            backgroundColor: 'rgba(70,190,80,0.1)',
            borderWidth: 2,
            pointRadius: 2,
            fill: true,
            tension: 0.3,
          }],
        },
        options: commonOptions,
      });
    }

    this.chartsReady = true;
    if (this.metrics.length) this._updateCharts();
  }

  private _updateCharts(): void {
    const labels = this.metrics.map(m => String(m.episode));
    const rewards = this.metrics.map(m => m.avgReward);
    const wins = this.metrics.map(m => +(m.winRate * 100).toFixed(1));

    if (this.rewardChart) {
      this.rewardChart.data.labels = labels;
      this.rewardChart.data.datasets[0].data = rewards;
      this.rewardChart.update('none');
    }

    if (this.winChart) {
      this.winChart.data.labels = labels;
      this.winChart.data.datasets[0].data = wins;
      this.winChart.update('none');
    }
  }
}
