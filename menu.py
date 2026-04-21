import pygame
import sys
import math
from pygame.locals import *

BG_DARK=(10,12,20); BG_CARD=(18,22,35)
ACCENT_BLUE=(64,156,255); ACCENT_RED=(255,75,75); ACCENT_GOLD=(255,200,50)
TEXT_WHITE=(230,235,255); TEXT_DIM=(100,110,140); BORDER=(35,45,70)
BTN_NORMAL=(22,30,52); BTN_HOVER=(32,50,90)

pygame.font.init()


def load_fonts(scale=1.0):
    sz=lambda n: max(10,int(n*scale))
    try:
        return {
            'title':    pygame.font.SysFont('couriernew',sz(64),bold=True),
            'subtitle': pygame.font.SysFont('couriernew',sz(17)),
            'btn':      pygame.font.SysFont('couriernew',sz(21),bold=True),
            'small':    pygame.font.SysFont('couriernew',sz(13)),
            'label':    pygame.font.SysFont('couriernew',sz(15)),
        }
    except:
        return {
            'title':    pygame.font.Font(None,sz(72)),
            'subtitle': pygame.font.Font(None,sz(22)),
            'btn':      pygame.font.Font(None,sz(26)),
            'small':    pygame.font.Font(None,sz(18)),
            'label':    pygame.font.Font(None,sz(20)),
        }


class Button:
    def __init__(self,x,y,w,h,text,accent=None):
        self.rect=pygame.Rect(x,y,w,h); self.text=text
        self.accent=accent or ACCENT_BLUE; self.hovered=False; self._pulse=0

    def draw(self,screen,fonts):
        self._pulse=(self._pulse+2)%360
        bg=BTN_HOVER if self.hovered else BTN_NORMAL
        pygame.draw.rect(screen,bg,self.rect,border_radius=8)
        pygame.draw.rect(screen,self.accent if self.hovered else BORDER,self.rect,2,border_radius=8)
        if self.hovered:
            g=int(8+4*math.sin(math.radians(self._pulse)))
            glow=pygame.Surface((self.rect.w+g*2,self.rect.h+g*2),pygame.SRCALPHA)
            for i in range(g,0,-2):
                pygame.draw.rect(glow,(*self.accent,int(50*i/g)),
                                 (g-i,g-i,self.rect.w+i*2,self.rect.h+i*2),border_radius=10)
            screen.blit(glow,(self.rect.x-g,self.rect.y-g))
        col=self.accent if self.hovered else TEXT_WHITE
        lbl=fonts['btn'].render(self.text,True,col)
        screen.blit(lbl,(self.rect.centerx-lbl.get_width()//2, self.rect.centery-lbl.get_height()//2))

    def check_hover(self,pos): self.hovered=self.rect.collidepoint(pos)
    def is_clicked(self,pos,event):
        return event.type==MOUSEBUTTONDOWN and event.button==1 and self.rect.collidepoint(pos)


def _build_bg(sw,sh):
    surf=pygame.Surface((sw,sh)); surf.fill(BG_DARK)
    sq=42
    for row in range(sh//sq+2):
        for col in range(sw//sq+2):
            if (row+col)%2==0:
                pygame.draw.rect(surf,(14,18,28),(col*sq,row*sq,sq,sq))
    return surf


def _build_vignette(sw,sh):
    v=pygame.Surface((sw,sh),pygame.SRCALPHA)
    for margin,alpha in [(0,80),(sw//8,50),(sw//5,25),(sw//3,10)]:
        pygame.draw.rect(v,(0,0,0,alpha),(margin,margin,sw-margin*2,sh-margin*2),margin//2+1)
    return v


def run_menu():
    pygame.init()
    info=pygame.display.Info()
    SW,SH=info.current_w,info.current_h
    screen=pygame.display.set_mode((SW,SH),pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
    pygame.display.set_caption("Checkers AI — Main Menu")
    clock=pygame.time.Clock()

    scale=min(SW/1280,SH/720)
    fonts=load_fonts(scale)

    bg_surf   = _build_bg(SW,SH)
    vignette  = _build_vignette(SW,SH)
    fade_surf = pygame.Surface((SW,SH)); fade_surf.fill((0,0,0))

    cx=SW//2
    panel_w=min(720,int(SW*0.58)); panel_x=cx-panel_w//2

    title_y  = int(SH*0.10)
    diff_py  = int(SH*0.44)
    mode_py  = int(SH*0.63)
    footer_y = SH-28

    difficulties = ['Easy','Medium','Hard','Expert']
    diff_depths  = {'Easy':1,'Medium':2,'Hard':3,'Expert':5}
    diff_descs   = {
        'Easy':   'Depth 1  ·  Random-like play, easy to beat',
        'Medium': 'Depth 2  ·  Basic strategy, good for beginners',
        'Hard':   'Depth 3  ·  Strong play, challenging opponent',
        'Expert': 'Depth 5  ·  Maximum strength, very hard to beat',
    }
    selected_diff='Medium'

    btn_w=max(130,int(panel_w*0.22)); btn_h=max(46,int(SH*0.065))
    gap=max(12,int(panel_w*0.02))
    total_bw=4*btn_w+3*gap; diff_start_x=cx-total_bw//2

    diff_buttons=[
        Button(diff_start_x+i*(btn_w+gap),diff_py+38,btn_w,btn_h,d,
               accent=ACCENT_RED if d=='Expert' else ACCENT_BLUE)
        for i,d in enumerate(difficulties)
    ]

    mode_w=max(240,int(panel_w*0.42)); mode_h=max(54,int(SH*0.075))
    pvai_btn=Button(cx-mode_w-14, mode_py+38, mode_w, mode_h,"▶  PLAYER  vs  AI",accent=ACCENT_BLUE)
    avai_btn=Button(cx+14,        mode_py+38, mode_w, mode_h,"▶  AI  vs  AI",    accent=ACCENT_RED)
    quit_btn=Button(cx-90,        int(SH*0.89),180,   36,    "QUIT",             accent=TEXT_DIM)

    # Fade-in state
    intro_alpha = 255.0  # starts opaque, fades to 0

    # Exit state
    exiting     = False
    exit_timer  = 0.0
    exit_target = None

    tick=0

    while True:
        dt=clock.tick(60)/1000.0
        tick+=1
        mp=pygame.mouse.get_pos()

        for b in diff_buttons: b.check_hover(mp)
        pvai_btn.check_hover(mp); avai_btn.check_hover(mp); quit_btn.check_hover(mp)

        for event in pygame.event.get():
            if event.type==QUIT or (event.type==KEYDOWN and event.key==K_ESCAPE):
                if not exiting:
                    exiting=True; exit_timer=0.0; exit_target='quit'
            if not exiting:
                for i,b in enumerate(diff_buttons):
                    if b.is_clicked(mp,event): selected_diff=difficulties[i]
                if pvai_btn.is_clicked(mp,event):
                    exiting=True; exit_timer=0.0
                    exit_target=('human_vs_ai',diff_depths[selected_diff])
                if avai_btn.is_clicked(mp,event):
                    exiting=True; exit_timer=0.0
                    exit_target=('ai_vs_ai',diff_depths[selected_diff])
                if quit_btn.is_clicked(mp,event):
                    exiting=True; exit_timer=0.0; exit_target='quit'

        # ── Draw ──
        screen.blit(bg_surf,(0,0))
        screen.blit(vignette,(0,0))

        # Title
        glow_a=int(150+80*math.sin(tick*0.04))
        t1=fonts['title'].render("CHECKERS",True,TEXT_WHITE)
        t2=fonts['title'].render("AI",True,ACCENT_BLUE)
        tw=t1.get_width()+t2.get_width()+16; tx=cx-tw//2
        screen.blit(t1,(tx,title_y))
        gs=pygame.Surface((t2.get_width()+20,t2.get_height()+10),pygame.SRCALPHA)
        gs.blit(fonts['title'].render("AI",True,(*ACCENT_BLUE,glow_a)),(10,5))
        screen.blit(gs,(tx+t1.get_width()+16-10,title_y-5))
        screen.blit(t2,(tx+t1.get_width()+16,title_y))

        sub=fonts['subtitle'].render(
            "Classic Draughts  ·  Minimax  ·  Alpha-Beta Pruning  ·  Game Tree Visualization",
            True,TEXT_DIM)
        screen.blit(sub,(cx-sub.get_width()//2,title_y+t1.get_height()+10))

        line_y=title_y+t1.get_height()+38
        pygame.draw.line(screen,BORDER,(cx-panel_w//2,line_y),(cx+panel_w//2,line_y))
        for dx in [-panel_w//2,panel_w//2]:
            pygame.draw.circle(screen,ACCENT_GOLD,(cx+dx,line_y),3)

        # Difficulty panel
        pygame.draw.rect(screen,BG_CARD,(panel_x,diff_py,panel_w,btn_h+90),border_radius=10)
        pygame.draw.rect(screen,ACCENT_GOLD,(panel_x,diff_py,panel_w,btn_h+90),1,border_radius=10)
        screen.blit(fonts['label'].render("SELECT DIFFICULTY",True,ACCENT_GOLD),(panel_x+16,diff_py-10))

        for i,b in enumerate(diff_buttons):
            is_sel=difficulties[i]==selected_diff
            if is_sel:
                pa=int(60+40*math.sin(tick*0.06))
                gs2=pygame.Surface((b.rect.w+20,b.rect.h+20),pygame.SRCALPHA)
                for r in range(10,0,-2):
                    pygame.draw.rect(gs2,(*ACCENT_GOLD,int(pa*r/10)),
                                     (10-r,10-r,b.rect.w+r*2,b.rect.h+r*2),border_radius=10)
                screen.blit(gs2,(b.rect.x-10,b.rect.y-10))
                pygame.draw.rect(screen,ACCENT_GOLD,b.rect.inflate(4,4),2,border_radius=10)
            b.draw(screen,fonts)

        # Difficulty description
        desc=fonts['small'].render(diff_descs[selected_diff],True,TEXT_DIM)
        screen.blit(desc,(panel_x+16, diff_py+btn_h+26))
        di=fonts['small'].render(
            f"Search depth: {diff_depths[selected_diff]}  |  Alpha-Beta Pruning enabled",
            True,TEXT_DIM)
        screen.blit(di,(panel_x+16,diff_py+btn_h+44))

        # Mode panel
        pygame.draw.rect(screen,BG_CARD,(panel_x,mode_py,panel_w,mode_h+70),border_radius=10)
        pygame.draw.rect(screen,ACCENT_BLUE,(panel_x,mode_py,panel_w,mode_h+70),1,border_radius=10)
        screen.blit(fonts['label'].render("SELECT MODE",True,ACCENT_BLUE),(panel_x+16,mode_py-10))
        pvai_btn.draw(screen,fonts); avai_btn.draw(screen,fonts)
        screen.blit(fonts['small'].render("You play as BLUE",True,TEXT_DIM),
                    (pvai_btn.rect.x,pvai_btn.rect.bottom+8))
        screen.blit(fonts['small'].render("Watch AIs + Tree Visualization",True,TEXT_DIM),
                    (avai_btn.rect.x,avai_btn.rect.bottom+8))

        quit_btn.draw(screen,fonts)
        ver=fonts['small'].render("Checkers-AI  ·  Minimax + α-β Pruning  ·  v2.0",True,TEXT_DIM)
        screen.blit(ver,(cx-ver.get_width()//2,footer_y))

        # Fade-in overlay
        if intro_alpha>0:
            fade_surf.set_alpha(int(intro_alpha))
            screen.blit(fade_surf,(0,0))
            intro_alpha=max(0.0, intro_alpha-dt*510)

        # Exit fade-out overlay
        if exiting:
            exit_timer+=dt
            fade_a=int(255*min(1.0,exit_timer/0.35))
            fade_surf.set_alpha(fade_a)
            screen.blit(fade_surf,(0,0))
            if exit_timer>=0.35:
                if exit_target=='quit':
                    pygame.quit(); sys.exit()
                return exit_target

        pygame.display.flip()