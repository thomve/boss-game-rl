import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FighterState, AbilityState } from '../../../services/game.service';

@Component({
  selector: 'app-fighter-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './fighter-panel.component.html',
  styleUrls: ['./fighter-panel.component.scss'],
})
export class FighterPanelComponent implements OnChanges {
  @Input() fighter!: FighterState;
  @Input() isPlayer = true;
  @Input() qValues: number[] | null = null;
  @Input() watchMode = false;

  hpPercent = 100;
  manaPercent = 100;
  hpClass = 'high';
  maxQValue = 0;

  ngOnChanges(): void {
    if (this.fighter) {
      this.hpPercent = Math.max(0, (this.fighter.hp / this.fighter.maxHp) * 100);
      this.manaPercent = Math.max(0, (this.fighter.mana / this.fighter.maxMana) * 100);

      if (this.hpPercent > 50) this.hpClass = 'high';
      else if (this.hpPercent > 25) this.hpClass = 'medium';
      else this.hpClass = 'low';

      if (this.qValues && this.qValues.length) {
        this.maxQValue = Math.max(...this.qValues.map(v => Math.abs(v)));
      }
    }
  }

  getQBar(index: number): number {
    if (!this.qValues || !this.maxQValue) return 0;
    const val = this.qValues[index];
    return Math.max(0, (val / this.maxQValue) * 100);
  }

  getQColor(index: number): string {
    if (!this.qValues) return '#333';
    const val = this.qValues[index];
    return val >= 0 ? 'var(--gold)' : 'var(--red-dim)';
  }

  trackByName(_: number, item: AbilityState): string {
    return item.name;
  }
}
