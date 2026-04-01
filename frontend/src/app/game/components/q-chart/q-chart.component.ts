import { Component, Input, OnChanges, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import type { Chart as ChartJS } from 'chart.js';

const ABILITY_NAMES = ['Strike', 'Power Slash', 'Heal', 'Poison Blade', 'Shield Up'];
const ABILITY_COLORS_AVAIL = ['#e6c35a', '#d24141', '#46be50', '#9b59b6', '#4a9edd'];
const ABILITY_COLORS_UNAVAIL = ['#555540', '#553030', '#305530', '#442255', '#253344'];

@Component({
    selector: 'app-q-chart',
    imports: [CommonModule],
    templateUrl: './q-chart.component.html',
    styleUrls: ['./q-chart.component.scss']
})
export class QChartComponent implements OnChanges, AfterViewInit {
  @Input() qValues: number[] | null = null;
  @Input() actionMask: number[] = [1, 1, 1, 1, 1];
  @ViewChild('chartCanvas') chartCanvas!: ElementRef<HTMLCanvasElement>;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private chart: ChartJS | null = null;
  private chartLoaded = false;

  ngAfterViewInit(): void {
    this._initChart();
  }

  ngOnChanges(): void {
    if (this.chartLoaded && this.qValues) {
      this._updateChart();
    }
  }

  private async _initChart(): Promise<void> {
    // Dynamically import Chart.js to avoid SSR issues
    const { Chart, BarController, CategoryScale, LinearScale, BarElement, Tooltip } = await import('chart.js');
    Chart.register(BarController, CategoryScale, LinearScale, BarElement, Tooltip);

    const ctx = this.chartCanvas?.nativeElement?.getContext('2d');
    if (!ctx) return;

    this.chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ABILITY_NAMES,
        datasets: [{
          label: 'Q-Value',
          data: this.qValues || [0, 0, 0, 0, 0],
          backgroundColor: this._getColors(),
          borderColor: this._getBorderColors(),
          borderWidth: 1,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 200 },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => `Q: ${(ctx.raw as number).toFixed(3)}`,
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: '#8888aa',
              font: { family: 'Rajdhani', size: 11 },
              maxRotation: 30,
            },
            grid: { color: 'rgba(255,255,255,0.04)' },
          },
          y: {
            ticks: { color: '#8888aa', font: { family: 'Rajdhani', size: 10 } },
            grid: { color: 'rgba(255,255,255,0.06)' },
          },
        },
      },
    });

    this.chartLoaded = true;
    if (this.qValues) this._updateChart();
  }

  private _updateChart(): void {
    if (!this.chart) return;
    this.chart.data.datasets[0].data = this.qValues || [0, 0, 0, 0, 0];
    this.chart.data.datasets[0].backgroundColor = this._getColors();
    this.chart.data.datasets[0].borderColor = this._getBorderColors();
    this.chart.update('none');
  }

  private _getColors(): string[] {
    return ABILITY_NAMES.map((_, i) =>
      (this.actionMask?.[i] ?? 1) ? ABILITY_COLORS_AVAIL[i] : ABILITY_COLORS_UNAVAIL[i]
    );
  }

  private _getBorderColors(): string[] {
    return this._getColors();
  }
}
