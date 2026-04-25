import pygame
import sys
import math
from pygame.locals import *

BG_DARK    = (10,  12,  20)
BG_CARD    = (18,  22,  35)
ACCENT_BLUE= (64, 156, 255)
ACCENT_RED = (255,  75,  75)
ACCENT_GOLD= (255, 200,  50)
TEXT_WHITE = (230, 235, 255)
TEXT_BODY  = (180, 188, 210)   # brighter than TEXT_DIM for readability
TEXT_DIM   = (100, 110, 140)
BORDER     = (35,  45,  70)
BTN_NORMAL = (22,  30,  52)
BTN_HOVER  = (32,  50,  90)

pygame.font.init()


def load_fonts(scale=1.0):
    sz = lambda n: max(10, int(n * scale))
    try:
        return {
            'title':    pygame.font.SysFont('couriernew', sz(60), bold=True),
            'subtitle': pygame.font.SysFont('couriernew', sz(15)),
            'btn':      pygame.font.SysFont('couriernew', sz(19), bold=True),
            'label':    pygame.font.SysFont('couriernew', sz(13), bold=True),
            'body':     pygame.font.SysFont('couriernew', sz(13)),
            'small':    pygame.font.SysFont('couriernew', sz(12)),
        }
    except:
        return {
            'title':    pygame.font.Font(None, sz(70)),
            'subtitle': pygame.font.Font(None, sz(20)),
            'btn':      pygame.font.Font(None, sz(24)),
            'label':    pygame.font.Font(None, sz(18)),
            'body':     pygame.font.Font(None, sz(17)),
            'small':    pygame.font.Font(None, sz(16)),
        }


class Button:
    def __init__(self, x, y, w, h, text, accent=None):
        self.rect   = pygame.Rect(x, y, w, h)
        self.text   = text
        self.accent = accent or ACCENT_BLUE
        self.hovered= False
        self._pulse = 0

    def draw(self, screen, fonts):
        self._pulse = (self._pulse + 2) % 360
        bg  = BTN_HOVER if self.hovered else BTN_NORMAL
        pygame.draw.rect(screen, bg, self.rect, border_radius=7)
        border_col = self.accent if self.hovered else BORDER
        pygame.draw.rect(screen, border_col, self.rect, 2, border_radius=7)
        if self.hovered:
            g = int(6 + 3*math.sin(math.radians(self._pulse)))
            glow = pygame.Surface((self.rect.w+g*2, self.rect.h+g*2), pygame.SRCALPHA)
            for i in range(g, 0, -2):
                pygame.draw.rect(glow, (*self.accent, int(45*i/g)),
                                 (g-i, g-i, self.rect.w+i*2, self.rect.h+i*2), border_radius=9)
            screen.blit(glow, (self.rect.x-g, self.rect.y-g))
        col = self.accent if self.hovered else TEXT_WHITE
        lbl = fonts['btn'].render(self.text, True, col)
        screen.blit(lbl, (self.rect.centerx - lbl.get_width()//2,
                          self.rect.centery - lbl.get_height()//2))

    def check_hover(self, pos): self.hovered = self.rect.collidepoint(pos)
    def is_clicked(self, pos, event):
        return event.type == MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(pos)


def _build_bg(sw, sh):
    surf = pygame.Surface((sw, sh))
    surf.fill(BG_DARK)
    sq = 42
    for row in range(sh//sq + 2):
        for col in range(sw//sq + 2):
            if (row + col) % 2 == 0:
                pygame.draw.rect(surf, (14, 18, 28), (col*sq, row*sq, sq, sq))
    return surf


def _build_vignette(sw, sh):
    v = pygame.Surface((sw, sh), pygame.SRCALPHA)
    for margin, alpha in [(0,80), (sw//8,50), (sw//5,25), (sw//3,10)]:
        pygame.draw.rect(v, (0,0,0,alpha),
                         (margin, margin, sw-margin*2, sh-margin*2), margin//2+1)
    return v


def _draw_panel(screen, x, y, w, h, label, label_color, border_color, fonts):
    """Draw a card panel. The label sits INSIDE the panel at the top — no clipping."""
    pygame.draw.rect(screen, BG_CARD, (x, y, w, h), border_radius=10)
    pygame.draw.rect(screen, border_color, (x, y, w, h), 2, border_radius=10)
    # Label bar at top of panel (background strip so it reads cleanly)
    lbl_surf = fonts['label'].render(label, True, label_color)
    lbl_x = x + 14
    lbl_y = y + 10                        # 10px inside the panel top edge
    pygame.draw.rect(screen, BG_CARD,
                     (lbl_x - 4, lbl_y - 2, lbl_surf.get_width()+8, lbl_surf.get_height()+4))
    screen.blit(lbl_surf, (lbl_x, lbl_y))


def run_menu():
    pygame.init()
    info = pygame.display.Info()
    SW, SH = info.current_w, info.current_h
    screen = pygame.display.set_mode((SW, SH),
                                     pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("Checkers AI — Main Menu")
    clock = pygame.time.Clock()

    scale  = min(SW/1280, SH/720)
    fonts  = load_fonts(scale)
    bg_surf   = _build_bg(SW, SH)
    vignette  = _build_vignette(SW, SH)
    fade_surf = pygame.Surface((SW, SH)); fade_surf.fill((0,0,0))

    cx = SW // 2

    # ── Panel geometry — calculated top-down so nothing overflows ──
    PANEL_W = min(700, int(SW * 0.56))
    PANEL_X = cx - PANEL_W // 2
    PAD     = 16       # inner padding

    # Title block
    TITLE_Y  = int(SH * 0.08)

    # Difficulty panel starts here
    DIFF_Y   = int(SH * 0.40)
    DIFF_LABEL_H  = fonts['label'].get_height() + 20   # label + top padding
    BTN_H    = max(42, int(SH * 0.060))
    BTN_ROW_H= BTN_H + 10                              # buttons + small gap below
    DESC_H   = fonts['body'].get_height() * 2 + 8      # two text lines
    DIFF_H   = DIFF_LABEL_H + BTN_ROW_H + DESC_H + PAD # total panel height

    # Mode panel starts just below difficulty panel with a gap
    MODE_Y   = DIFF_Y + DIFF_H + 14
    MODE_LABEL_H = fonts['label'].get_height() + 20
    MODE_BTN_H   = max(48, int(SH * 0.068))
    MODE_DESC_H  = fonts['body'].get_height() + 8
    MODE_H   = MODE_LABEL_H + MODE_BTN_H + MODE_DESC_H + PAD

    # QUIT button
    QUIT_Y   = MODE_Y + MODE_H + 18
    FOOTER_Y = SH - 24

    # ── Difficulty buttons ──
    difficulties = ['Easy', 'Medium', 'Hard', 'Expert']
    diff_depths  = {'Easy':1, 'Medium':2, 'Hard':3, 'Expert':5}
    diff_descs   = {
        'Easy':   'Depth 1  ·  Quick play, easy to beat',
        'Medium': 'Depth 2  ·  Basic strategy, good for beginners',
        'Hard':   'Depth 3  ·  Strong play, challenging',
        'Expert': 'Depth 5  ·  Maximum strength, very hard',
    }
    selected_diff = 'Medium'

    # 4 buttons share PANEL_W - 2*PAD width with 3 gaps between them
    dbtn_gap  = 8
    dbtn_w    = (PANEL_W - 2*PAD - 3*dbtn_gap) // 4
    dbtn_y    = DIFF_Y + DIFF_LABEL_H          # buttons start after label row
    diff_buttons = [
        Button(PANEL_X + PAD + i*(dbtn_w+dbtn_gap), dbtn_y, dbtn_w, BTN_H, d,
               accent=ACCENT_RED if d=='Expert' else ACCENT_BLUE)
        for i, d in enumerate(difficulties)
    ]

    # ── Mode buttons ──
    # Two buttons side by side inside the panel, each half-width minus gap
    mbtn_gap = 10
    mbtn_w   = (PANEL_W - 2*PAD - mbtn_gap) // 2
    mbtn_y   = MODE_Y + MODE_LABEL_H
    pvai_btn = Button(PANEL_X + PAD,               mbtn_y, mbtn_w, MODE_BTN_H,
                      "PLAYER  vs  AI", accent=ACCENT_BLUE)
    avai_btn = Button(PANEL_X + PAD + mbtn_w + mbtn_gap, mbtn_y, mbtn_w, MODE_BTN_H,
                      "AI  vs  AI",     accent=ACCENT_RED)

    quit_btn = Button(cx-80, QUIT_Y, 160, 36, "QUIT", accent=TEXT_DIM)

    intro_alpha = 255.0
    exiting     = False
    exit_timer  = 0.0
    exit_target = None
    tick = 0

    while True:
        dt   = clock.tick(60) / 1000.0
        tick += 1
        mp   = pygame.mouse.get_pos()

        for b in diff_buttons: b.check_hover(mp)
        pvai_btn.check_hover(mp)
        avai_btn.check_hover(mp)
        quit_btn.check_hover(mp)

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                if not exiting:
                    exiting=True; exit_timer=0.0; exit_target='quit'
            if not exiting:
                for i, b in enumerate(diff_buttons):
                    if b.is_clicked(mp, event): selected_diff = difficulties[i]
                if pvai_btn.is_clicked(mp, event):
                    exiting=True; exit_timer=0.0
                    exit_target=('human_vs_ai', diff_depths[selected_diff])
                if avai_btn.is_clicked(mp, event):
                    exiting=True; exit_timer=0.0
                    exit_target=('ai_vs_ai', diff_depths[selected_diff])
                if quit_btn.is_clicked(mp, event):
                    exiting=True; exit_timer=0.0; exit_target='quit'

        # ── Draw background ──
        screen.blit(bg_surf, (0,0))
        screen.blit(vignette, (0,0))

        # ── Title ──
        glow_a = int(150 + 80*math.sin(tick*0.04))
        t1 = fonts['title'].render("CHECKERS", True, TEXT_WHITE)
        t2 = fonts['title'].render("AI",       True, ACCENT_BLUE)
        tw = t1.get_width() + t2.get_width() + 14
        tx = cx - tw//2
        screen.blit(t1, (tx, TITLE_Y))
        # Glow behind "AI"
        gsurf = pygame.Surface((t2.get_width()+16, t2.get_height()+8), pygame.SRCALPHA)
        gsurf.blit(fonts['title'].render("AI", True, (*ACCENT_BLUE, glow_a)), (8,4))
        screen.blit(gsurf, (tx + t1.get_width() + 14 - 8, TITLE_Y - 4))
        screen.blit(t2, (tx + t1.get_width() + 14, TITLE_Y))

        sub = fonts['subtitle'].render(
            "Classic Draughts  ·  Minimax  ·  Alpha-Beta Pruning  ·  Game Tree Visualization",
            True, TEXT_DIM)
        sub_y = TITLE_Y + t1.get_height() + 8
        screen.blit(sub, (cx - sub.get_width()//2, sub_y))

        # Decorative line
        line_y = sub_y + sub.get_height() + 14
        pygame.draw.line(screen, BORDER, (PANEL_X, line_y), (PANEL_X+PANEL_W, line_y))
        for dx in [0, PANEL_W]:
            pygame.draw.circle(screen, ACCENT_GOLD, (PANEL_X+dx, line_y), 3)

        # ── Difficulty panel ──
        _draw_panel(screen, PANEL_X, DIFF_Y, PANEL_W, DIFF_H,
                    "SELECT DIFFICULTY", ACCENT_GOLD, ACCENT_GOLD, fonts)

        # Difficulty buttons
        for i, b in enumerate(diff_buttons):
            is_sel = difficulties[i] == selected_diff
            if is_sel:
                pa = int(55 + 35*math.sin(tick*0.06))
                gs2 = pygame.Surface((b.rect.w+16, b.rect.h+16), pygame.SRCALPHA)
                for r in range(8, 0, -2):
                    pygame.draw.rect(gs2, (*ACCENT_GOLD, int(pa*r/8)),
                                     (8-r, 8-r, b.rect.w+r*2, b.rect.h+r*2), border_radius=9)
                screen.blit(gs2, (b.rect.x-8, b.rect.y-8))
                pygame.draw.rect(screen, ACCENT_GOLD, b.rect.inflate(4,4), 2, border_radius=9)
            b.draw(screen, fonts)

        # Description lines below buttons — bright enough to read
        desc_y = dbtn_y + BTN_H + 10
        desc = fonts['body'].render(diff_descs[selected_diff], True, TEXT_BODY)
        screen.blit(desc, (PANEL_X + PAD, desc_y))
        di = fonts['body'].render(
            f"Search depth: {diff_depths[selected_diff]}  |  Alpha-Beta Pruning",
            True, TEXT_BODY)
        screen.blit(di, (PANEL_X + PAD, desc_y + desc.get_height() + 4))

        # ── Mode panel ──
        _draw_panel(screen, PANEL_X, MODE_Y, PANEL_W, MODE_H,
                    "SELECT MODE", ACCENT_BLUE, ACCENT_BLUE, fonts)

        pvai_btn.draw(screen, fonts)
        avai_btn.draw(screen, fonts)

        # Descriptions below mode buttons
        mdesc_y = mbtn_y + MODE_BTN_H + 8
        screen.blit(fonts['small'].render("You play as BLUE", True, TEXT_BODY),
                    (pvai_btn.rect.x, mdesc_y))
        screen.blit(fonts['small'].render("Watch AIs + Tree View", True, TEXT_BODY),
                    (avai_btn.rect.x, mdesc_y))

        # ── Quit + Footer ──
        quit_btn.draw(screen, fonts)
        ver = fonts['small'].render(
            "Checkers-AI  ·  Minimax + α-β Pruning  ·  v2.0", True, TEXT_DIM)
        screen.blit(ver, (cx - ver.get_width()//2, FOOTER_Y))

        # ── Fade overlays ──
        if intro_alpha > 0:
            fade_surf.set_alpha(int(intro_alpha))
            screen.blit(fade_surf, (0,0))
            intro_alpha = max(0.0, intro_alpha - dt*510)

        if exiting:
            exit_timer += dt
            fade_surf.set_alpha(int(255*min(1.0, exit_timer/0.35)))
            screen.blit(fade_surf, (0,0))
            if exit_timer >= 0.35:
                if exit_target == 'quit':
                    pygame.quit(); sys.exit()
                return exit_target

        pygame.display.flip()