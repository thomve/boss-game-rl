import { Component, Input, OnChanges, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';

interface LogEntry {
  text: string;
  cssClass: string;
}

@Component({
  selector: 'app-combat-log',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './combat-log.component.html',
  styleUrls: ['./combat-log.component.scss'],
})
export class CombatLogComponent implements OnChanges, AfterViewChecked {
  @Input() logs: string[] = [];
  @ViewChild('logContainer') logContainer!: ElementRef<HTMLDivElement>;

  parsedLogs: LogEntry[] = [];
  private needsScroll = false;

  ngOnChanges(): void {
    this.parsedLogs = (this.logs || []).map(line => ({
      text: line,
      cssClass: this._classify(line),
    }));
    this.needsScroll = true;
  }

  ngAfterViewChecked(): void {
    if (this.needsScroll) {
      this._scrollToBottom();
      this.needsScroll = false;
    }
  }

  private _scrollToBottom(): void {
    try {
      const el = this.logContainer?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    } catch { /* ignore */ }
  }

  private _classify(line: string): string {
    const l = line.toLowerCase();
    if (l.includes('=== turn')) return 'log-turn';
    if (l.includes('hero uses') || l.includes('hero heals') || l.includes('hero gains')) return 'log-player';
    if (l.includes('dragon') && (l.includes('uses') || l.includes('heals') || l.includes('gains'))) return 'log-boss';
    if (l.includes('defeated') || l.includes('succumbs') || l.includes("time's up")) return 'log-result';
    if (l.includes('poison') || l.includes('regen') || l.includes('effect') || l.includes('-- effects --')) return 'log-effect';
    if (l.includes('stunned') || l.includes('enraged') || l.includes('afflicted')) return 'log-status';
    if (l.includes('damage') || l.includes('takes')) return 'log-damage';
    return 'log-neutral';
  }
}
