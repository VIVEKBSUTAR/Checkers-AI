import pygame
import sys
import math
import time
from pygame.locals import *
from copy import deepcopy
import checkers
import gamebot

WHITE=(255,255,255); BLUE=(0,0,255); RED=(255,0,0); BLACK=(0,0,0); GOLD=(255,215,0)
BG_DARK=(10,12,20); BG_CARD=(16,20,32)
ACCENT_BLUE=(64,156,255); ACCENT_RED=(255,75,75); ACCENT_GOLD=(255,200,50); ACCENT_GREEN=(50,220,120)
TEXT_WHITE=(230,235,255); TEXT_DIM=(100,110,140); PANEL_BG=(14,18,30); BORDER=(35,45,70)
REJECTED_BG=(30,16,16); REJECTED_BD=(120,40,40); CHOSEN_BD=(50,200,100)
PIECE_BLUE=(30,80,220); PIECE_BLUE_HI=(100,150,255); PIECE_RED=(200,30,30); PIECE_RED_HI=(255,100,80)

# Phase constants
PHASE_READY    = 0
PHASE_SLIDE    = 1
PHASE_CTRLSIN  = 2
PHASE_GAMEPLAY = 3

pygame.font.init()


def _draw_piece(surface, color, cx, cy, r, king=False):
    fill   = PIECE_BLUE    if color==BLUE else PIECE_RED
    hi_col = PIECE_BLUE_HI if color==BLUE else PIECE_RED_HI
    pygame.draw.circle(surface, BLACK, (cx,cy), r+1)
    pygame.draw.circle(surface, fill,  (cx,cy), r)
    hs = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
    pygame.draw.circle(hs, (*hi_col,110),(r//2,r//2), max(1,r//2))
    surface.blit(hs,(cx-r+r//4, cy-r+r//4))
    if king:
        sr,ir = max(3,r//3), max(2,r//6)
        pts=[(cx+int((sr if k%2==0 else ir)*math.cos(math.radians(k*36-90))),
              cy+int((sr if k%2==0 else ir)*math.sin(math.radians(k*36-90)))) for k in range(10)]
        pygame.draw.polygon(surface, GOLD, pts)
        pygame.draw.polygon(surface, BLACK,pts,1)


def _draw_checkers_board(surface, board, x, y, size):
    sq = size // 8
    for row in range(8):
        for col in range(8):
            c = (200,160,110) if (row+col)%2==0 else (80,50,28)
            pygame.draw.rect(surface, c, (x+col*sq, y+row*sq, sq, sq))
    r = max(4, sq//2-3)
    for row in range(8):
        for col in range(8):
            occ = board.matrix[col][row].occupant
            if occ:
                _draw_piece(surface, occ.color, x+col*sq+sq//2, y+row*sq+sq//2, r, king=occ.king)


def _draw_mini_board(surface, board, x, y, size, fonts, chosen=False, rejected=False, label=None, score=None):
    sq = max(1, size // 8)
    bd = CHOSEN_BD if chosen else (REJECTED_BD if rejected else BORDER)
    bg = (14,28,20) if chosen else (REJECTED_BG if rejected else BG_CARD)
    pygame.draw.rect(surface, bg, (x-2,y-2,size+4,size+4), border_radius=4)
    pygame.draw.rect(surface, bd, (x-2,y-2,size+4,size+4), 2, border_radius=4)

    if rejected:
        pygame.draw.line(surface, REJECTED_BD,(x+4,y+4),(x+size-4,y+size-4),2)
        pygame.draw.line(surface, REJECTED_BD,(x+size-4,y+4),(x+4,y+size-4),2)
        if fonts:
            t=fonts['tiny'].render("PRUNED",True,REJECTED_BD)
            surface.blit(t,(x+size//2-t.get_width()//2, y+size//2-8))
            t2=fonts['tiny'].render("α-β cut",True,REJECTED_BD)
            surface.blit(t2,(x+size//2-t2.get_width()//2,y+size//2+4))
    elif board is not None:
        for row in range(8):
            for col in range(8):
                c=(180,140,100) if (row+col)%2==0 else (70,45,25)
                pygame.draw.rect(surface,c,(x+col*sq,y+row*sq,sq,sq))
        r=max(3,sq//2-2)
        for row in range(8):
            for col in range(8):
                occ=board.matrix[col][row].occupant
                if occ:
                    _draw_piece(surface,occ.color,x+col*sq+sq//2,y+row*sq+sq//2,r,king=occ.king)

    if label and fonts:
        lt=fonts['tiny'].render(label,True,ACCENT_GOLD if chosen else TEXT_DIM)
        surface.blit(lt,(x+size//2-lt.get_width()//2, y-14))
    if score is not None and fonts and not rejected:
        sv = min(999, max(-999, int(score)))
        sc = f"score:{sv:+d}"
        st=fonts['tiny'].render(sc,True,ACCENT_GREEN if chosen else TEXT_DIM)
        surface.blit(st,(x+size//2-st.get_width()//2, y+size+2))


class Slider:
    def __init__(self,x,y,w,min_v,max_v,init,label):
        self.rect=pygame.Rect(x,y,w,16); self.min=min_v; self.max=max_v
        self.value=init; self.label=label; self.dragging=False; self.disabled=False

    def draw(self,surface,fonts):
        col=TEXT_DIM if self.disabled else ACCENT_BLUE
        pygame.draw.rect(surface,BORDER,self.rect,border_radius=4)
        if not self.disabled:
            frac=(self.value-self.min)/(self.max-self.min)
            fw=int(frac*self.rect.w)
            if fw>0: pygame.draw.rect(surface,col,(self.rect.x,self.rect.y,fw,self.rect.h),border_radius=4)
            kx=self.rect.x+fw
            pygame.draw.circle(surface,TEXT_WHITE,(kx,self.rect.centery),8)
            pygame.draw.circle(surface,col,(kx,self.rect.centery),6)
        val_str = '--' if self.disabled else f'{self.value:.1f}s'
        t=fonts['tiny'].render(f"{self.label}: {val_str}",True,col)
        surface.blit(t,(self.rect.x,self.rect.y-14))

    def handle_event(self,event):
        if self.disabled: return
        if event.type==MOUSEBUTTONDOWN and event.button==1 and self.rect.inflate(10,10).collidepoint(event.pos):
            self.dragging=True
        if event.type==MOUSEBUTTONUP: self.dragging=False
        if event.type==MOUSEMOTION and self.dragging:
            frac=max(0.,min(1.,(event.pos[0]-self.rect.x)/self.rect.w))
            self.value=round(self.min+frac*(self.max-self.min),1)


def _btn(surface, rect, label, hovered, fonts, accent=ACCENT_BLUE, bg=PANEL_BG):
    pygame.draw.rect(surface,bg,rect,border_radius=5)
    pygame.draw.rect(surface,accent if hovered else BORDER,rect,2,border_radius=5)
    t=fonts['sm'].render(label,True,accent if hovered else TEXT_WHITE)
    surface.blit(t,(rect.centerx-t.get_width()//2,rect.centery-t.get_height()//2))


def run_ai_vs_ai(depth):
    pygame.init()
    info=pygame.display.Info()
    SW,SH=info.current_w,info.current_h
    screen=pygame.display.set_mode((SW,SH),pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
    pygame.display.set_caption("Checkers AI — AI vs AI  ·  Game Tree Visualization")
    clock=pygame.time.Clock()

    scale=min(SW/1280,SH/720)
    sz=lambda n: max(10,int(n*scale))
    try:
        font_xl  =pygame.font.SysFont('couriernew',sz(22),bold=True)
        font_lg  =pygame.font.SysFont('couriernew',sz(17),bold=True)
        font_sm  =pygame.font.SysFont('couriernew',sz(13))
        font_tiny=pygame.font.SysFont('couriernew',sz(11))
    except:
        font_xl=pygame.font.Font(None,sz(28)); font_lg=pygame.font.Font(None,sz(22))
        font_sm=pygame.font.Font(None,sz(17)); font_tiny=pygame.font.Font(None,sz(14))
    fonts={'xl':font_xl,'lg':font_lg,'sm':font_sm,'tiny':font_tiny}

    # ── Layout ──
    BX      = int(SW*0.02)
    BOARD_H = int(SH*0.56); BOARD_H=(BOARD_H//8)*8
    BY      = int(SH*0.08)
    BOARD_W = BOARD_H
    TREE_X  = int(SW*0.46)
    TREE_W  = SW - TREE_X - int(SW*0.01)

    MINI_GAP  = max(8, int(TREE_W*0.02))
    MINI_SIZE = max(80,(TREE_W - 3*MINI_GAP)//4); MINI_SIZE=(MINI_SIZE//8)*8
    TOP_ROW_Y = BY + 40

    CTRL_Y = SH - int(SH*0.10)
    BTN_H  = min(38, max(28, int(SH*0.042)))
    BTN_W  = max(130, int(SW*0.10))
    gap    = 10

    SLIDER_Y = max(BY+BOARD_H+50, CTRL_Y - BTN_H - 30)

    # Slide animation start position (centered)
    START_BX = SW//2 - BOARD_W//2
    START_BY = SH//2 - BOARD_H//2

    def make_game():
        g=checkers.Game(loop_mode=True,skip_graphics=True)
        bb=gamebot.Bot(g,BLUE,mid_eval='piece_and_board',end_eval='sum_of_dist',method='alpha_beta',depth=depth)
        br=gamebot.Bot(g,RED, mid_eval='piece_and_board',end_eval='sum_of_dist',method='alpha_beta',depth=depth)
        return g,bb,br

    game,bot_blue,bot_red = make_game()

    slider = Slider(BX, SLIDER_Y, int(SW*0.18), 0.1, 3.0, 0.8, "Delay")

    # Control button rects
    r_restart   = pygame.Rect(SW-BTN_W-gap,          CTRL_Y,           BTN_W, BTN_H)
    r_pause     = pygame.Rect(SW-BTN_W*2-gap*2,       CTRL_Y,           BTN_W, BTN_H)
    r_step_tog  = pygame.Rect(SW-BTN_W*3-gap*3,       CTRL_Y,           BTN_W, BTN_H)
    r_next_move = pygame.Rect(SW-BTN_W*2-gap*2,       CTRL_Y+BTN_H+gap, BTN_W*2+gap, BTN_H)
    r_back      = pygame.Rect(SW-BTN_W-gap,           CTRL_Y+BTN_H+gap, BTN_W, BTN_H)

    # ── State ──
    phase         = PHASE_READY
    phase_elapsed = 0.0

    tree_nodes     = []
    rejected_nodes = []
    move_count     = 0
    nodes_explored = 0
    last_move_time = time.time()
    game_over      = False
    winner         = None
    paused         = False
    step_mode      = False
    step_triggered = False

    phase4_elapsed        = 0.0
    move_flash_timer      = 0.0
    step_mode_announce_t  = 0.0
    exiting               = False
    exit_timer            = 0.0

    # Pre-build fade surface (no SRCALPHA — use set_alpha)
    fade_surf = pygame.Surface((SW,SH)); fade_surf.fill((0,0,0))

    def get_bot():
        return bot_blue if game.turn==BLUE else bot_red

    def do_step():
        nonlocal tree_nodes,rejected_nodes,nodes_explored,move_count,phase4_elapsed,move_flash_timer
        bot=get_bot()
        top,rej=bot.get_top_candidates(game.board,n=4)
        nodes_explored=bot._count_nodes; move_count+=1
        tree_nodes=[{
            'board':c['board_clone'],
            'score':c['score'],
            'chosen':i==0,
            'label':f"{'★ CHOSEN' if i==0 else f'Option {i+1}'}",
        } for i,c in enumerate(top)]
        rejected_nodes=rej
        phase4_elapsed=0.0
        move_flash_timer=0.4

    # ── Main loop ──
    while True:
        dt = clock.tick(60)/1000.0
        mp = pygame.mouse.get_pos()

        # ── Events ──
        for event in pygame.event.get():
            if event.type==QUIT:
                pygame.quit(); sys.exit()
            if event.type==KEYDOWN:
                if event.key==K_ESCAPE and not exiting:
                    exiting=True; exit_timer=0.0
                if event.key==K_SPACE and phase==PHASE_GAMEPLAY and not step_mode:
                    paused=not paused
                if event.key==K_RIGHT and phase==PHASE_GAMEPLAY and step_mode and not game_over:
                    step_triggered=True

            if phase==PHASE_GAMEPLAY and not exiting:
                slider.handle_event(event)
                if event.type==MOUSEBUTTONDOWN and event.button==1:
                    if r_back.collidepoint(mp) and not exiting:
                        exiting=True; exit_timer=0.0
                    if r_restart.collidepoint(mp):
                        game,bot_blue,bot_red=make_game()
                        tree_nodes=[];rejected_nodes=[];move_count=0;nodes_explored=0
                        last_move_time=time.time();game_over=False;winner=None;paused=False
                        phase4_elapsed=0.0;move_flash_timer=0.0
                    if r_pause.collidepoint(mp) and not step_mode:
                        paused=not paused
                    if r_step_tog.collidepoint(mp):
                        step_mode=not step_mode
                        slider.disabled=step_mode
                        paused=False
                        if step_mode: step_mode_announce_t=1.5
                    if r_next_move.collidepoint(mp) and step_mode and not game_over:
                        step_triggered=True

        # ── Phase state machine ──
        phase_elapsed += dt

        if phase==PHASE_READY and phase_elapsed>=1.0:
            phase=PHASE_SLIDE; phase_elapsed=0.0
        elif phase==PHASE_SLIDE and phase_elapsed>=0.6:
            phase=PHASE_CTRLSIN; phase_elapsed=0.0
        elif phase==PHASE_CTRLSIN and phase_elapsed>=0.4:
            phase=PHASE_GAMEPLAY; phase_elapsed=0.0; last_move_time=time.time()

        # ── AI step logic (only in GAMEPLAY) ──
        if phase==PHASE_GAMEPLAY and not game_over and not exiting:
            if step_mode:
                if step_triggered:
                    do_step(); step_triggered=False
                    if game.endit:
                        game_over=True
                        winner=game.winner or ("BLUE" if game.turn==RED else "RED")
            else:
                if not paused:
                    now=time.time()
                    if now-last_move_time>=slider.value:
                        do_step(); last_move_time=time.time()
                        if game.endit:
                            game_over=True
                            winner=game.winner or ("BLUE" if game.turn==RED else "RED")

        # ── Timers ──
        phase4_elapsed   = max(0.0, phase4_elapsed + dt)
        move_flash_timer = max(0.0, move_flash_timer - dt)
        step_mode_announce_t = max(0.0, step_mode_announce_t - dt)
        if exiting:
            exit_timer += dt

        # ── Compute board position for phases ──
        if phase==PHASE_READY:
            cur_bx,cur_by = START_BX,START_BY
            panel_alpha   = 0
            ctrl_alpha    = 0
        elif phase==PHASE_SLIDE:
            t_s  = min(1.0, phase_elapsed/0.6)
            ease = 1-(1-t_s)**3
            cur_bx = int(START_BX + (BX-START_BX)*ease)
            cur_by = int(START_BY + (BY-START_BY)*ease)
            panel_alpha = int(255*ease)
            ctrl_alpha  = 0
        elif phase==PHASE_CTRLSIN:
            cur_bx,cur_by = BX,BY
            panel_alpha   = 255
            ctrl_alpha    = int(255*min(1.0, phase_elapsed/0.4))
        else:
            cur_bx,cur_by = BX,BY
            panel_alpha   = 255
            ctrl_alpha    = 255

        # ══ DRAW ══
        screen.fill(BG_DARK)

        # Ambient gold border glow around board
        ambient_a = int(10 + 6*math.sin(pygame.time.get_ticks()*0.002))
        glow_surf = pygame.Surface((BOARD_W+12, BOARD_H+12), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*ACCENT_GOLD, ambient_a), (0,0,BOARD_W+12,BOARD_H+12), 3, border_radius=6)
        screen.blit(glow_surf, (cur_bx-6, cur_by-6))

        # Main board
        pygame.draw.rect(screen,BG_CARD,(cur_bx-3,cur_by-3,BOARD_W+6,BOARD_H+6),border_radius=6)
        _draw_checkers_board(screen, game.board, cur_bx, cur_by, BOARD_W)

        # Move flash overlay
        if move_flash_timer>0:
            flash_a = int(160*(move_flash_timer/0.4))
            flash_s = pygame.Surface((BOARD_W,BOARD_H), pygame.SRCALPHA)
            flash_s.fill((50,220,120,flash_a))
            screen.blit(flash_s,(cur_bx,cur_by))

        # Board border
        pygame.draw.rect(screen,ACCENT_GOLD,(cur_bx-3,cur_by-3,BOARD_W+6,BOARD_H+6),2,border_radius=6)

        # Board title
        tc = ACCENT_BLUE if game.turn==BLUE else ACCENT_RED
        ts = "BLUE's turn" if game.turn==BLUE else "RED's turn"
        if game_over: ts=f"{winner} WINS!"; tc=ACCENT_GOLD
        tl=font_lg.render(f"LIVE GAME  ·  {ts}",True,tc)
        screen.blit(tl,(cur_bx, cur_by-28))

        # Stats (two lines)
        sy=cur_by+BOARD_H+10
        screen.blit(font_sm.render(f"Move: {move_count}   Depth: {depth}",True,TEXT_DIM),(cur_bx,sy))
        screen.blit(font_sm.render(f"Nodes explored: {nodes_explored}",True,TEXT_DIM),(cur_bx,sy+16))

        # Game over overlay on board
        if game_over:
            ov=pygame.Surface((BOARD_W,BOARD_H)); ov.fill((0,0,0)); ov.set_alpha(170)
            screen.blit(ov,(cur_bx,cur_by))
            wc=ACCENT_BLUE if winner=="BLUE" else ACCENT_RED
            wt=font_xl.render(f"{winner} WINS!",True,wc)
            screen.blit(wt,(cur_bx+BOARD_W//2-wt.get_width()//2, cur_by+BOARD_H//2-20))
            st=font_sm.render("Press ↺ RESTART",True,TEXT_DIM)
            screen.blit(st,(cur_bx+BOARD_W//2-st.get_width()//2, cur_by+BOARD_H//2+20))

        # Paused overlay
        if paused and not game_over and phase==PHASE_GAMEPLAY:
            ov=pygame.Surface((BOARD_W,BOARD_H)); ov.fill((0,0,0)); ov.set_alpha(140)
            screen.blit(ov,(cur_bx,cur_by))
            pt=font_xl.render("PAUSED",True,ACCENT_GOLD)
            screen.blit(pt,(cur_bx+BOARD_W//2-pt.get_width()//2, cur_by+BOARD_H//2-pt.get_height()//2))

        # PHASE_READY special overlay
        if phase==PHASE_READY:
            t_ready = min(1.0, phase_elapsed/0.5)
            title_a = int(255*t_ready)
            title_s = pygame.Surface((SW,60)); title_s.fill(BG_DARK); title_s.set_alpha(0)
            tt=font_xl.render("AI  vs  AI", True, ACCENT_GOLD)
            ts2=font_sm.render("Initializing game tree visualization...", True, TEXT_DIM)
            # Draw with alpha using SRCALPHA surfaces
            ts_surf=pygame.Surface((tt.get_width(),tt.get_height()), pygame.SRCALPHA)
            ts_surf.blit(tt,(0,0)); ts_surf.set_alpha(title_a)
            screen.blit(ts_surf,(SW//2-tt.get_width()//2, cur_by-60))
            ts2_surf=pygame.Surface((ts2.get_width(),ts2.get_height()), pygame.SRCALPHA)
            ts2_surf.blit(ts2,(0,0)); ts2_surf.set_alpha(title_a)
            screen.blit(ts2_surf,(SW//2-ts2.get_width()//2, cur_by+BOARD_H+10))

        # ── Tree panel (fades in during PHASE_SLIDE+) ──
        if panel_alpha>0:
            # Header (clip to TREE_W)
            th_surf=font_xl.render("DECISION TREE  —  Top 4 Candidate Moves",True,ACCENT_GOLD)
            if th_surf.get_width()>TREE_W:
                th_surf=font_lg.render("DECISION TREE  —  Top 4",True,ACCENT_GOLD)
            th_container=pygame.Surface((th_surf.get_width(),th_surf.get_height()), pygame.SRCALPHA)
            th_container.blit(th_surf,(0,0)); th_container.set_alpha(panel_alpha)
            screen.blit(th_container,(TREE_X,BY-32))
            pygame.draw.line(screen,(*BORDER, panel_alpha) if panel_alpha<255 else BORDER,
                             (TREE_X,BY-8),(SW-10,BY-8))

            if tree_nodes:
                total_w=4*MINI_SIZE+3*MINI_GAP
                root_cx=TREE_X+total_w//2
                boards_y=TOP_ROW_Y+32

                # Root dot
                pygame.draw.circle(screen,ACCENT_GOLD,(root_cx,TOP_ROW_Y+6),5)
                rl=font_tiny.render("current position",True,TEXT_DIM)
                screen.blit(rl,(root_cx-rl.get_width()//2,TOP_ROW_Y-8))

                # 4 candidate mini boards with stagger animation
                for i,node in enumerate(tree_nodes):
                    bx2 = TREE_X + i*(MINI_SIZE+MINI_GAP)
                    bc2 = bx2+MINI_SIZE//2

                    delay_i = i*0.08
                    board_elapsed_i = max(0.0, phase4_elapsed - delay_i)
                    t_i   = min(1.0, board_elapsed_i/0.35)
                    ease_i = 1-(1-t_i)**2
                    alpha_i  = int(255*ease_i)
                    y_off_i  = int(20*(1.0-ease_i))

                    # Connector line (fades with board)
                    if alpha_i>0:
                        lc=CHOSEN_BD if node['chosen'] else BORDER
                        line_s=pygame.Surface((SW,SH), pygame.SRCALPHA)
                        pygame.draw.line(line_s,(*lc,alpha_i),(root_cx,TOP_ROW_Y+14),(bc2,boards_y-2),1)
                        screen.blit(line_s,(0,0))

                    # Mini board on temp surface with slide+fade
                    if alpha_i>0:
                        tmp_h=MINI_SIZE+50
                        tmp=pygame.Surface((MINI_SIZE+40,tmp_h), pygame.SRCALPHA)
                        score_val=node['score']
                        if score_val==float('inf'): score_val=999
                        _draw_mini_board(tmp,node['board'],20,20+y_off_i,MINI_SIZE,fonts,
                                         chosen=node['chosen'],label=node['label'],score=score_val)
                        tmp.set_alpha(alpha_i)
                        screen.blit(tmp,(bx2-20, boards_y-20))

                        # Pulsing border on chosen board
                        if node['chosen'] and alpha_i==255:
                            pulse_a=int(100+80*math.sin(pygame.time.get_ticks()*0.003))
                            pb=pygame.Surface((MINI_SIZE+14,MINI_SIZE+14), pygame.SRCALPHA)
                            pygame.draw.rect(pb,(*CHOSEN_BD,pulse_a),(0,0,MINI_SIZE+14,MINI_SIZE+14),3,border_radius=6)
                            screen.blit(pb,(bx2-7, boards_y-7))

                # Rejected section (appears after ~0.6s)
                rej_elapsed = phase4_elapsed - 0.6
                rej_alpha   = int(255*min(1.0,max(0.0,rej_elapsed/0.3)))
                if rej_alpha>0 and rejected_nodes:
                    rej_y=boards_y+MINI_SIZE+50
                    rej_surf=pygame.Surface((TREE_W+20,120)); rej_surf.fill(BG_DARK); rej_surf.set_alpha(rej_alpha)
                    screen.blit(rej_surf,(TREE_X-10,rej_y-35))
                    rl2=font_sm.render(f"α-β PRUNED: {len(rejected_nodes)} moves",True,REJECTED_BD)
                    rl2_s=pygame.Surface((rl2.get_width(),rl2.get_height()),pygame.SRCALPHA)
                    rl2_s.blit(rl2,(0,0)); rl2_s.set_alpha(rej_alpha)
                    screen.blit(rl2_s,(TREE_X,rej_y-30))
                    pygame.draw.line(screen,REJECTED_BD,(TREE_X,rej_y-14),(TREE_X+TREE_W,rej_y-14),1)
                    rej_mini=max(50,MINI_SIZE//2)
                    for i in range(min(6,len(rejected_nodes))):
                        rx=TREE_X+i*(rej_mini+MINI_GAP)
                        if rx+rej_mini>SW-10: break
                        rtmp=pygame.Surface((rej_mini+10,rej_mini+10),pygame.SRCALPHA)
                        _draw_mini_board(rtmp,None,5,5,rej_mini,fonts,rejected=True)
                        rtmp.set_alpha(rej_alpha)
                        screen.blit(rtmp,(rx-5,rej_y-5))
            else:
                wt=font_lg.render("Waiting for first AI move...",True,TEXT_DIM)
                wt_s=pygame.Surface((wt.get_width(),wt.get_height()),pygame.SRCALPHA)
                wt_s.blit(wt,(0,0)); wt_s.set_alpha(panel_alpha)
                screen.blit(wt_s,(TREE_X+20,TOP_ROW_Y+40))

        # ── Controls (fade in during PHASE_CTRLSIN+) ──
        if ctrl_alpha>0:
            slider.disabled=step_mode
            # Draw slider with alpha via temp surface
            sl_tmp=pygame.Surface((int(SW*0.18)+20,30)); sl_tmp.fill(BG_DARK); sl_tmp.set_alpha(ctrl_alpha)
            screen.blit(sl_tmp,(slider.rect.x-5,slider.rect.y-16))
            slider.draw(screen,fonts)

            _btn(screen,r_restart,"↺ RESTART",   r_restart.collidepoint(mp),  fonts,ACCENT_BLUE)
            _btn(screen,r_back,   "← MENU",      r_back.collidepoint(mp),     fonts,TEXT_DIM)
            step_lbl="AUTO PLAY" if step_mode else "STEP MODE"
            _btn(screen,r_step_tog,step_lbl,r_step_tog.collidepoint(mp),fonts,ACCENT_GOLD)

            if step_mode:
                _btn(screen,r_next_move,"▶  NEXT MOVE",r_next_move.collidepoint(mp),fonts,ACCENT_GREEN)
                ht=font_tiny.render("or press → key",True,TEXT_DIM)
                screen.blit(ht,(r_next_move.x, r_next_move.bottom+4))
            else:
                pl="▶ RESUME" if paused else "⏸ PAUSE"
                _btn(screen,r_pause,pl,r_pause.collidepoint(mp),fonts,ACCENT_GOLD)

            # Apply ctrl fade
            if ctrl_alpha<255:
                ov=pygame.Surface((SW,SH)); ov.fill(BG_DARK); ov.set_alpha(255-ctrl_alpha)
                screen.blit(ov,(0,0))

        # Step mode announce overlay
        if step_mode_announce_t>0:
            ann_a=min(255,int(255*step_mode_announce_t))
            ann=pygame.Surface((BOARD_W,BOARD_H)); ann.fill((0,0,0)); ann.set_alpha(int(ann_a*0.7))
            screen.blit(ann,(cur_bx,cur_by))
            t1=font_xl.render("STEP MODE ACTIVE",True,ACCENT_GOLD)
            t2=font_sm.render("→ Click NEXT MOVE or press →",True,TEXT_WHITE)
            t1s=pygame.Surface((t1.get_width(),t1.get_height()),pygame.SRCALPHA); t1s.blit(t1,(0,0)); t1s.set_alpha(ann_a)
            t2s=pygame.Surface((t2.get_width(),t2.get_height()),pygame.SRCALPHA); t2s.blit(t2,(0,0)); t2s.set_alpha(ann_a)
            screen.blit(t1s,(cur_bx+BOARD_W//2-t1.get_width()//2, cur_by+BOARD_H//2-30))
            screen.blit(t2s,(cur_bx+BOARD_W//2-t2.get_width()//2, cur_by+BOARD_H//2+10))

        # Exit fade-out
        if exiting:
            fade_a=int(255*min(1.0,exit_timer/0.3))
            fade_surf.set_alpha(fade_a)
            screen.blit(fade_surf,(0,0))
            if exit_timer>=0.3:
                return

        pygame.display.flip()