"""
Pygame GUI for Boss Fight RL
==============================
Modes:
  Watch — trained DQN agent plays automatically (requires trained_agent.json)
  Play  — human selects abilities via buttons or keyboard (0-4)

Controls:
  R         — new game
  Space     — next turn (watch + manual mode)
  0-4       — use ability (play mode)
"""

import sys
import os
import pygame
import numpy as np
from environment import BossFightEnv
from agent import DQNAgent

# ── Window & timing ──────────────────────────────────────────────────────────
WIN_W, WIN_H  = 1100, 720
FPS           = 60
AGENT_PATH    = "trained_agent.json"
AUTO_DELAY_MS = 900   # ms between auto-steps in watch mode
RESTART_DELAY = 2500  # ms after game over before auto-restart in watch mode

# ── Colour palette ───────────────────────────────────────────────────────────
C_BG        = (18, 18, 28)
C_PANEL     = (32, 32, 48)
C_PANEL_ALT = (24, 24, 38)
C_BORDER    = (60, 60, 90)
C_TEXT      = (210, 210, 225)
C_DIM       = (130, 130, 155)
C_GOLD      = (230, 195, 90)
C_HP_HI     = (70, 190, 80)
C_HP_MID    = (200, 180, 50)
C_HP_LO     = (210, 65, 65)
C_MP        = (65, 120, 220)
C_BTN       = (50, 55, 80)
C_BTN_HOV   = (70, 75, 110)
C_BTN_DIS   = (30, 30, 45)
C_BTN_ON    = (55, 120, 75)
C_GREEN     = (70, 190, 80)
C_RED       = (210, 65, 65)
C_ORANGE    = (220, 140, 50)

EFFECT_COL = {
    "poison":   (130, 210, 90),
    "shield":   (80, 160, 230),
    "stunned":  (220, 190, 50),
    "regen":    (80, 220, 140),
    "enraged":  (230, 80,  60),
    "weakened": (180, 100, 210),
}


# ── Drawing helpers ──────────────────────────────────────────────────────────

def lerp_color(a, b, t):
    return tuple(int(a[i] + t * (b[i] - a[i])) for i in range(3))


def hp_color(ratio):
    if ratio > 0.6:
        return lerp_color(C_HP_MID, C_HP_HI, (ratio - 0.6) / 0.4)
    if ratio > 0.3:
        return lerp_color(C_HP_LO, C_HP_MID, (ratio - 0.3) / 0.3)
    return C_HP_LO


def draw_bar(surf, x, y, w, h, value, maximum, bar_color=None, bg=(50, 30, 30)):
    ratio = max(0.0, min(1.0, value / maximum)) if maximum else 0.0
    pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=3)
    fill = max(0, int(w * ratio))
    if fill:
        col = bar_color if bar_color else hp_color(ratio)
        pygame.draw.rect(surf, col, (x, y, fill, h), border_radius=3)
    pygame.draw.rect(surf, C_BORDER, (x, y, w, h), 1, border_radius=3)


def draw_panel(surf, rect, color=None):
    pygame.draw.rect(surf, color or C_PANEL, rect, border_radius=6)
    pygame.draw.rect(surf, C_BORDER, rect, 1, border_radius=6)


# ── Button ────────────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect, label, font, *, enabled=True, active=False, color=None):
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.font    = font
        self.enabled = enabled
        self.active  = active
        self.color   = color

    def draw(self, surf, mouse):
        hov = self.rect.collidepoint(mouse) and self.enabled
        if not self.enabled:
            bg = C_BTN_DIS
        elif self.active:
            bg = C_BTN_ON
        elif hov:
            bg = C_BTN_HOV
        else:
            bg = self.color or C_BTN
        pygame.draw.rect(surf, bg, self.rect, border_radius=5)
        pygame.draw.rect(surf, C_BORDER, self.rect, 1, border_radius=5)
        col = C_TEXT if self.enabled else C_DIM
        txt = self.font.render(self.label, True, col)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event, mouse):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.enabled
            and self.rect.collidepoint(mouse)
        )


# ── Main GUI ──────────────────────────────────────────────────────────────────

class BossFightGUI:

    HEADER_H = 55
    FOOTER_H = 120
    LEFT_W   = 300
    RIGHT_W  = 300

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Boss Fight RL")
        self.clock  = pygame.time.Clock()

        self.fnt_title = pygame.font.SysFont("segoeui", 28, bold=True)
        self.fnt_lg    = pygame.font.SysFont("segoeui", 20, bold=True)
        self.fnt_md    = pygame.font.SysFont("segoeui", 16)
        self.fnt_sm    = pygame.font.SysFont("segoeui", 13)
        self.fnt_xs    = pygame.font.SysFont("segoeui", 12)

        self.MAIN_Y = self.HEADER_H
        self.MAIN_H = WIN_H - self.HEADER_H - self.FOOTER_H
        self.MID_W  = WIN_W - self.LEFT_W - self.RIGHT_W   # 500

        # ── Environment & agent ─────────────────────────────────────────────
        self.env      = BossFightEnv()
        self.agent    = DQNAgent(
            state_size=self.env.n_observations,
            action_size=self.env.n_actions,
            hidden_sizes=[256, 128],
        )
        self.agent_ok = False
        if os.path.exists(AGENT_PATH):
            try:
                self.agent.load(AGENT_PATH)
                self.agent.epsilon = 0.0
                self.agent_ok = True
            except Exception:
                pass

        # ── UI state ────────────────────────────────────────────────────────
        self.mode       = "watch" if self.agent_ok else "play"
        self.auto_play  = True
        self.game_over  = False
        self.winner     = None
        self.q_values   = np.zeros(self.env.n_actions)
        self.combat_log = []
        self.last_step  = pygame.time.get_ticks()
        self.game_end_t = 0
        self.stun_timer = None   # scheduled auto-advance timestamp for stun

        self.state = self.env.reset()
        self._refresh()

    # ── State helpers ─────────────────────────────────────────────────────────

    def _refresh(self):
        self.rd = self.env.render()
        self._build_buttons()

    def _build_buttons(self):
        FOOT_Y = WIN_H - self.FOOTER_H + 8
        mask   = self.env.get_action_mask()
        abils  = self.rd["player"]["abilities"]
        n      = len(abils)
        btn_w  = 150
        gap    = 8
        total  = n * btn_w + (n - 1) * gap
        ax     = (WIN_W - total) // 2

        self.ability_btns = []
        for i, ab in enumerate(abils):
            avail = bool(mask[i])
            cd    = ab["cooldown"]
            mp    = ab["mana_cost"]
            if cd > 0:
                label = f"{ab['name']}  CD:{cd}"
            elif mp > 0:
                label = f"{ab['name']}  {int(mp)}mp"
            else:
                label = ab["name"]
            enabled = avail and self.mode == "play" and not self.game_over
            self.ability_btns.append(
                Button(
                    (ax + i * (btn_w + gap), FOOT_Y, btn_w, 36),
                    label, self.fnt_sm, enabled=enabled,
                )
            )

        ROW2_Y = FOOT_Y + 46
        cx = ax
        self.btn_watch = Button(
            (cx,       ROW2_Y, 140, 30), "Watch Agent",   self.fnt_sm,
            enabled=self.agent_ok, active=self.mode == "watch",
        )
        self.btn_play = Button(
            (cx + 148, ROW2_Y, 140, 30), "Play Yourself", self.fnt_sm,
            active=self.mode == "play",
        )
        self.btn_auto = Button(
            (cx + 308, ROW2_Y, 120, 30),
            "Auto: " + ("ON" if self.auto_play else "OFF"), self.fnt_sm,
            enabled=self.mode == "watch",
            active=self.auto_play and self.mode == "watch",
        )
        self.btn_next = Button(
            (cx + 436, ROW2_Y, 110, 30), "Next Turn", self.fnt_sm,
            enabled=(self.mode == "watch" and not self.auto_play and not self.game_over),
        )
        self.btn_reset = Button(
            (cx + 556, ROW2_Y, 110, 30), "New Game", self.fnt_sm,
        )

    # ── Game actions ──────────────────────────────────────────────────────────

    def _new_game(self):
        self.state      = self.env.reset()
        self.game_over  = False
        self.winner     = None
        self.q_values   = np.zeros(self.env.n_actions)
        self.combat_log = []
        self.last_step  = pygame.time.get_ticks()
        self.game_end_t = 0
        self.stun_timer = None
        self._refresh()

    def _do_step(self, action: int):
        if self.game_over:
            return
        old_len = len(self.env.game.log)
        self.state, _, done, info = self.env.step(action)
        self.combat_log.extend(self.env.game.log[old_len:])
        self.combat_log = self.combat_log[-300:]
        self._refresh()
        if done:
            self.game_over  = True
            self.winner     = info.get("winner")
            self.game_end_t = pygame.time.get_ticks()

    def _agent_step(self):
        mask          = self.env.get_action_mask()
        self.q_values = self.agent.get_q_values(self.state)
        action        = self.agent.choose_action(self.state, mask)
        self._do_step(action)

    def _player_step(self, idx: int):
        mask = self.env.get_action_mask()
        if idx < len(mask) and mask[idx]:
            self._do_step(idx)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw_header(self):
        pygame.draw.rect(self.screen, C_PANEL_ALT, (0, 0, WIN_W, self.HEADER_H))
        pygame.draw.line(self.screen, C_BORDER,
                         (0, self.HEADER_H - 1), (WIN_W, self.HEADER_H - 1))

        t = self.fnt_title.render("BOSS FIGHT  RL", True, C_GOLD)
        self.screen.blit(t, (20, (self.HEADER_H - t.get_height()) // 2))

        turn_s = f"Turn  {self.rd['turn']} / {self.env.game.MAX_TURNS}"
        t = self.fnt_md.render(turn_s, True, C_DIM)
        self.screen.blit(t, (WIN_W // 2 - t.get_width() // 2,
                              (self.HEADER_H - t.get_height()) // 2))

        if self.game_over:
            s   = "VICTORY!" if self.winner == "player" else "DEFEATED..."
            col = C_GREEN if self.winner == "player" else C_RED
            t   = self.fnt_lg.render(s, True, col)
        else:
            s   = "Watch Agent" if self.mode == "watch" else "Play Yourself"
            col = C_GREEN if self.mode == "watch" else C_ORANGE
            t   = self.fnt_md.render(s, True, col)
        self.screen.blit(t, (WIN_W - t.get_width() - 20,
                              (self.HEADER_H - t.get_height()) // 2))

    def _draw_fighter(self, x, y, w, h, data, is_player):
        """Draw HP/mana/effects block for one fighter. Returns next free y."""
        draw_panel(self.screen, (x, y, w, h))
        pad = 12

        # Name
        col = C_GOLD if is_player else C_RED
        t   = self.fnt_lg.render(data["name"], True, col)
        self.screen.blit(t, (x + pad, y + pad))
        cy  = y + pad + t.get_height() + 8

        # HP bar
        hp, mhp = data["hp"], data["max_hp"]
        hl  = self.fnt_sm.render("HP", True, C_DIM)
        self.screen.blit(hl, (x + pad, cy + 1))
        bx  = x + pad + hl.get_width() + 6
        bw  = w - pad - hl.get_width() - 6 - pad
        draw_bar(self.screen, bx, cy, bw, 16, hp, mhp, bg=(55, 25, 25))
        self.screen.blit(
            self.fnt_xs.render(f"{hp:.0f}/{mhp:.0f}", True, C_TEXT),
            (bx + 4, cy + 1),
        )
        cy += 22

        # Mana bar
        mp, mmp = data["mana"], data["max_mana"]
        ml  = self.fnt_sm.render("MP", True, C_DIM)
        self.screen.blit(ml, (x + pad, cy + 1))
        draw_bar(self.screen, bx, cy, bw, 16, mp, mmp,
                 bar_color=C_MP, bg=(20, 28, 60))
        self.screen.blit(
            self.fnt_xs.render(f"{mp:.0f}/{mmp:.0f}", True, C_TEXT),
            (bx + 4, cy + 1),
        )
        cy += 26

        # Effects
        effects = data.get("effects", [])
        self.screen.blit(self.fnt_sm.render("Effects", True, C_DIM), (x + pad, cy))
        cy += self.fnt_sm.get_height() + 4
        if effects:
            for eff in effects:
                ec = EFFECT_COL.get(eff["name"], C_TEXT)
                et = self.fnt_xs.render(
                    f"  {eff['name']}  ({eff['duration']}t)", True, ec
                )
                self.screen.blit(et, (x + pad, cy))
                cy += et.get_height() + 2
        else:
            none_t = self.fnt_xs.render("  none", True, C_DIM)
            self.screen.blit(none_t, (x + pad, cy))
            cy += none_t.get_height() + 2

        return cy

    def _draw_player_panel(self):
        x, y = 5, self.MAIN_Y + 5
        w, h = self.LEFT_W - 10, self.MAIN_H - 10
        cy   = self._draw_fighter(x, y, w, h, self.rd["player"], is_player=True)

        # ── Abilities list with inline Q-value bars ─────────────────────────
        cy += 8
        pygame.draw.line(self.screen, C_BORDER,
                         (x + 8, cy), (x + w - 8, cy))
        cy += 6
        self.screen.blit(
            self.fnt_sm.render("Abilities", True, C_DIM), (x + 12, cy)
        )
        cy += self.fnt_sm.get_height() + 6

        mask  = self.env.get_action_mask()
        abils = self.rd["player"]["abilities"]
        q     = self.q_values
        q_min = float(q.min())
        q_max = float(q.max())
        q_rng = max(q_max - q_min, 0.01)

        for i, ab in enumerate(abils):
            avail = bool(mask[i])
            col   = C_TEXT if avail else C_DIM

            cd_s = f" CD:{ab['cooldown']}" if ab["cooldown"] > 0 else ""
            mp_s = f" {int(ab['mana_cost'])}mp" if ab["mana_cost"] > 0 else ""
            lt   = self.fnt_xs.render(f"[{i}] {ab['name']}{mp_s}{cd_s}", True, col)
            self.screen.blit(lt, (x + 12, cy))

            # Small Q-value bar (watch mode only)
            if self.mode == "watch" and self.agent_ok:
                qv    = float(q[i])
                qnorm = (qv - q_min) / q_rng
                bar_x = x + w - 68
                bar_w_px = 52
                bar_h = 10
                bar_y = cy + 2
                pygame.draw.rect(self.screen, (40, 40, 55),
                                 (bar_x, bar_y, bar_w_px, bar_h), border_radius=2)
                fill = max(0, int(bar_w_px * qnorm))
                if fill:
                    bc = C_HP_HI if avail else (60, 100, 60)
                    pygame.draw.rect(self.screen, bc,
                                     (bar_x, bar_y, fill, bar_h), border_radius=2)
                self.screen.blit(
                    self.fnt_xs.render(f"{qv:+.1f}", True, C_DIM),
                    (bar_x + bar_w_px + 2, cy),
                )

            cy += lt.get_height() + 4

        # STUNNED notice
        if sum(mask) == 0 and not self.game_over:
            st = self.fnt_sm.render("STUNNED  — skipping turn", True, EFFECT_COL["stunned"])
            self.screen.blit(st, (x + 12, cy + 4))

    def _draw_boss_panel(self):
        x = self.LEFT_W + self.MID_W + 5
        y = self.MAIN_Y + 5
        w = self.RIGHT_W - 10
        h = self.MAIN_H - 10
        self._draw_fighter(x, y, w, h, self.rd["boss"], is_player=False)

    def _draw_log_panel(self):
        x  = self.LEFT_W + 3
        y  = self.MAIN_Y + 5
        w  = self.MID_W - 6
        h  = self.MAIN_H - 10

        # Reserve bottom section for Q-chart in watch mode
        show_qchart = self.mode == "watch" and self.agent_ok
        log_h = h - (145 if show_qchart else 0)

        # ── Combat log ─────────────────────────────────────────────────────
        draw_panel(self.screen, (x, y, w, log_h), color=C_PANEL_ALT)
        lh = self.fnt_md.render("Combat Log", True, C_GOLD)
        self.screen.blit(lh, (x + 10, y + 8))

        line_h    = 14
        max_lines = (log_h - 34) // line_h
        lines     = self.combat_log[-max_lines:] if self.combat_log else ["  Waiting for combat..."]
        ly        = y + 30
        for line in lines:
            s = line.strip()
            if not s:
                ly += 4
                continue
            if "===" in s:
                col = C_GOLD
            elif any(k in s for k in ("DEFEATED", "succumbs", "retreats")):
                col = C_RED
            elif any(k in s for k in ("heals", "regenerates")):
                col = C_GREEN
            elif any(k in s for k in ("STUNNED", "ENRAGED", "stun")):
                col = C_ORANGE
            elif "poison" in s.lower():
                col = EFFECT_COL["poison"]
            else:
                col = C_TEXT
            t = self.fnt_xs.render(s[:60], True, col)
            self.screen.blit(t, (x + 8, ly))
            ly += line_h

        if not show_qchart:
            return

        # ── Q-value bar chart ───────────────────────────────────────────────
        qy = y + log_h + 5
        qh = h - log_h - 5
        draw_panel(self.screen, (x, qy, w, qh), color=C_PANEL_ALT)
        qt = self.fnt_sm.render("Q-Values  (agent's scored actions)", True, C_DIM)
        self.screen.blit(qt, (x + 10, qy + 6))

        mask  = self.env.get_action_mask()
        abils = self.rd["player"]["abilities"]
        q     = self.q_values
        n     = len(q)
        q_min = float(q.min())
        q_max = float(q.max())
        q_rng = max(q_max - q_min, 0.01)

        chart_y = qy + 26
        chart_h = qh - 42
        bar_w   = (w - 20 - (n - 1) * 8) // n
        bx      = x + 10

        for i in range(n):
            avail  = bool(mask[i])
            qv     = float(q[i])
            qnorm  = (qv - q_min) / q_rng
            fill_h = max(2, int(chart_h * qnorm))

            # Bar background
            pygame.draw.rect(self.screen, (40, 40, 55),
                             (bx, chart_y, bar_w, chart_h), border_radius=3)
            # Bar fill (grows upward from bottom)
            bc  = C_HP_HI if avail else (60, 100, 60)
            by  = chart_y + chart_h - fill_h
            pygame.draw.rect(self.screen, bc,
                             (bx, by, bar_w, fill_h), border_radius=3)

            # Ability name label below bar
            name_s = abils[i]["name"][:7]
            nt = self.fnt_xs.render(name_s,
                                     True, C_TEXT if avail else C_DIM)
            self.screen.blit(nt, (bx + bar_w // 2 - nt.get_width() // 2,
                                   chart_y + chart_h + 2))

            # Q-value above bar
            qvt = self.fnt_xs.render(f"{qv:+.1f}", True, C_DIM)
            self.screen.blit(qvt, (bx + bar_w // 2 - qvt.get_width() // 2,
                                    max(chart_y + 2, by - 14)))
            bx += bar_w + 8

    def _draw_footer(self):
        fy    = WIN_H - self.FOOTER_H
        mouse = pygame.mouse.get_pos()
        pygame.draw.rect(self.screen, C_PANEL_ALT, (0, fy, WIN_W, self.FOOTER_H))
        pygame.draw.line(self.screen, C_BORDER, (0, fy), (WIN_W, fy))

        for btn in self.ability_btns:
            btn.draw(self.screen, mouse)
        self.btn_watch.draw(self.screen, mouse)
        self.btn_play.draw(self.screen, mouse)
        self.btn_auto.draw(self.screen, mouse)
        self.btn_next.draw(self.screen, mouse)
        self.btn_reset.draw(self.screen, mouse)

        # Hint bar
        hint = (
            "Keys:  R = new game   |   0-4 = use ability (play mode)"
            "   |   Space = next turn (watch / manual)"
        )
        ht = self.fnt_xs.render(hint, True, C_DIM)
        self.screen.blit(ht, (WIN_W // 2 - ht.get_width() // 2, WIN_H - 14))

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._new_game()
                    elif event.key == pygame.K_SPACE:
                        if self.mode == "watch" and not self.auto_play and not self.game_over:
                            self._agent_step()
                    elif pygame.K_0 <= event.key <= pygame.K_4:
                        if self.mode == "play" and not self.game_over:
                            self._player_step(event.key - pygame.K_0)

                if self.btn_watch.clicked(event, mouse):
                    self.mode = "watch"
                    self.stun_timer = None
                    self._build_buttons()

                elif self.btn_play.clicked(event, mouse):
                    self.mode = "play"
                    self.stun_timer = None
                    self._build_buttons()

                elif self.btn_auto.clicked(event, mouse):
                    self.auto_play = not self.auto_play
                    self.last_step = pygame.time.get_ticks()
                    self._build_buttons()

                elif self.btn_next.clicked(event, mouse):
                    self._agent_step()

                elif self.btn_reset.clicked(event, mouse):
                    self._new_game()

                else:
                    for i, btn in enumerate(self.ability_btns):
                        if btn.clicked(event, mouse) and self.mode == "play":
                            self._player_step(i)
                            break

            now = pygame.time.get_ticks()

            # ── Auto-play (watch mode) ──────────────────────────────────────
            if self.mode == "watch" and self.auto_play:
                if self.game_over:
                    if now - self.game_end_t >= RESTART_DELAY:
                        self._new_game()
                elif now - self.last_step >= AUTO_DELAY_MS:
                    self._agent_step()
                    self.last_step = now

            # ── Auto-skip stunned turn (play mode) ─────────────────────────
            if self.mode == "play" and not self.game_over:
                if sum(self.env.get_action_mask()) == 0:
                    if self.stun_timer is None:
                        self.stun_timer = now + 800
                else:
                    self.stun_timer = None

            if self.stun_timer and now >= self.stun_timer:
                self.stun_timer = None
                self._do_step(0)

            # ── Render ─────────────────────────────────────────────────────
            self.screen.fill(C_BG)
            self._draw_header()
            self._draw_player_panel()
            self._draw_boss_panel()
            self._draw_log_panel()
            self._draw_footer()
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    BossFightGUI().run()
