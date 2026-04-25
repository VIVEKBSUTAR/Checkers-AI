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

PHASE_READY=0; PHASE_SLIDE=1; PHASE_CTRLSIN=2; PHASE_GAMEPLAY=3

pygame.font.init()


def _draw_piece(surface, color, cx, cy, r, king=False):
    fill   = PIECE_BLUE    if color==BLUE else PIECE_RED
    hi_col = PIECE_BLUE_HI if color==BLUE else PIECE_RED_HI
    pygame.draw.circle(surface,BLACK,(cx,cy),r+1)
    pygame.draw.circle(surface,fill, (cx,cy),r)
    hs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
    pygame.draw.circle(hs,(*hi_col,110),(r//2,r//2),max(1,r//2))
    surface.blit(hs,(cx-r+r//4,cy-r+r//4))
    if king:
        sr,ir=max(3,r//3),max(2,r//6)
        pts=[(cx+int((sr if k%2==0 else ir)*math.cos(math.radians(k*36-90))),
              cy+int((sr if k%2==0 else ir)*math.sin(math.radians(k*36-90)))) for k in range(10)]
        pygame.draw.polygon(surface,GOLD,pts); pygame.draw.polygon(surface,BLACK,pts,1)


def _draw_checkers_board(surface, board, x, y, size):
    sq=size//8
    for row in range(8):
        for col in range(8):
            c=(200,160,110) if (row+col)%2==0 else (80,50,28)
            pygame.draw.rect(surface,c,(x+col*sq,y+row*sq,sq,sq))
    r=max(4,sq//2-3)
    for row in range(8):
        for col in range(8):
            occ=board.matrix[col][row].occupant
            if occ:
                _draw_piece(surface,occ.color,x+col*sq+sq//2,y+row*sq+sq//2,r,king=occ.king)


def _draw_mini_board(surface, board, x, y, size, font_tiny, chosen=False, rejected=False, label=None, score=None):
    """Draw a mini board. label drawn ABOVE (y-16), score BELOW (y+size+3). Caller must reserve space."""
    sq=max(1,size//8)
    bd=CHOSEN_BD if chosen else (REJECTED_BD if rejected else BORDER)
    bg=(14,28,20) if chosen else (REJECTED_BG if rejected else BG_CARD)

    pygame.draw.rect(surface,bg,(x,y,size,size),border_radius=3)
    pygame.draw.rect(surface,bd,(x,y,size,size),2,border_radius=3)

    if rejected:
        pygame.draw.line(surface,REJECTED_BD,(x+4,y+4),(x+size-4,y+size-4),2)
        pygame.draw.line(surface,REJECTED_BD,(x+size-4,y+4),(x+4,y+size-4),2)
        t=font_tiny.render("PRUNED",True,REJECTED_BD)
        surface.blit(t,(x+size//2-t.get_width()//2, y+size//2-t.get_height()-2))
        t2=font_tiny.render("α-β cut",True,REJECTED_BD)
        surface.blit(t2,(x+size//2-t2.get_width()//2,y+size//2+2))
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

    # Label above board
    if label:
        lt=font_tiny.render(label,True,ACCENT_GOLD if chosen else TEXT_DIM)
        surface.blit(lt,(x+size//2-lt.get_width()//2, y-lt.get_height()-2))

    # Score below board
    if score is not None and not rejected:
        sv=min(999,max(-999,int(score)))
        st=font_tiny.render(f"score:{sv:+d}",True,ACCENT_GREEN if chosen else TEXT_DIM)
        surface.blit(st,(x+size//2-st.get_width()//2, y+size+3))


class Slider:
    def __init__(self,x,y,w,min_v,max_v,init,label):
        self.rect=pygame.Rect(x,y,w,14); self.min=min_v; self.max=max_v
        self.value=init; self.label=label; self.dragging=False; self.disabled=False

    def draw(self,surface,font):
        col=TEXT_DIM if self.disabled else ACCENT_BLUE
        pygame.draw.rect(surface,BORDER,self.rect,border_radius=3)
        if not self.disabled:
            frac=(self.value-self.min)/(self.max-self.min)
            fw=int(frac*self.rect.w)
            if fw>0: pygame.draw.rect(surface,col,(self.rect.x,self.rect.y,fw,self.rect.h),border_radius=3)
            kx=self.rect.x+fw
            pygame.draw.circle(surface,TEXT_WHITE,(kx,self.rect.centery),7)
            pygame.draw.circle(surface,col,(kx,self.rect.centery),5)
        val_str='--' if self.disabled else f'{self.value:.1f}s'
        t=font.render(f"{self.label}: {val_str}",True,col)
        surface.blit(t,(self.rect.x, self.rect.y-t.get_height()-2))

    def handle_event(self,event):
        if self.disabled: return
        if event.type==MOUSEBUTTONDOWN and event.button==1 and self.rect.inflate(10,10).collidepoint(event.pos):
            self.dragging=True
        if event.type==MOUSEBUTTONUP: self.dragging=False
        if event.type==MOUSEMOTION and self.dragging:
            frac=max(0.,min(1.,(event.pos[0]-self.rect.x)/self.rect.w))
            self.value=round(self.min+frac*(self.max-self.min),1)


def _btn(surface, rect, label, hovered, font, accent=ACCENT_BLUE):
    pygame.draw.rect(surface, PANEL_BG, rect, border_radius=5)
    pygame.draw.rect(surface, accent if hovered else BORDER, rect, 2, border_radius=5)
    t=font.render(label, True, accent if hovered else TEXT_WHITE)
    surface.blit(t,(rect.centerx-t.get_width()//2, rect.centery-t.get_height()//2))


def run_ai_vs_ai(depth):
    pygame.init()
    info=pygame.display.Info()
    SW,SH=info.current_w,info.current_h
    screen=pygame.display.set_mode((SW,SH),pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
    pygame.display.set_caption("Checkers AI — AI vs AI  ·  Game Tree Visualization")
    clock=pygame.time.Clock()

    scale=min(SW/1280,SH/720)
    sz=lambda n: max(9,int(n*scale))

    try:
        font_xl  =pygame.font.SysFont('couriernew',sz(19),bold=True)
        font_lg  =pygame.font.SysFont('couriernew',sz(15),bold=True)
        font_sm  =pygame.font.SysFont('couriernew',sz(12))
        font_tiny=pygame.font.SysFont('couriernew',sz(10))
    except:
        font_xl=pygame.font.Font(None,sz(24)); font_lg=pygame.font.Font(None,sz(20))
        font_sm=pygame.font.Font(None,sz(16)); font_tiny=pygame.font.Font(None,sz(13))

    # ── Fixed zone heights ──
    TOP_BAR_H  = max(36, int(SH*0.052))   # title bar at top
    CTRL_H     = max(80, int(SH*0.115))   # control strip at bottom
    CONTENT_Y  = TOP_BAR_H                # content starts here
    CONTENT_H  = SH - TOP_BAR_H - CTRL_H # content area height
    CTRL_Y     = SH - CTRL_H             # control strip starts here

    # ── Left panel: board ──
    BX       = int(SW*0.02)
    LEFT_W   = int(SW*0.36)              # left panel total width
    BOARD_W  = min(LEFT_W - int(SW*0.01), CONTENT_H - 40)
    BOARD_W  = (BOARD_W//8)*8
    BY       = CONTENT_Y + (CONTENT_H - BOARD_W)//2  # vertically centred in content area

    # ── Right panel: tree ──
    DIVIDER_X = BX + BOARD_W + int(SW*0.015)
    TREE_X    = DIVIDER_X + 8
    TREE_W    = SW - TREE_X - int(SW*0.01)

    # ── Mini board sizing: 4 boards + 3 gaps fit in TREE_W ──
    MINI_GAP  = max(6, int(TREE_W*0.013))
    MINI_SIZE = (TREE_W - 3*MINI_GAP) // 4
    MINI_SIZE = (MINI_SIZE//8)*8
    MINI_SIZE = max(72, MINI_SIZE)

    # ── Tree vertical layout ──
    LABEL_H   = font_tiny.get_height() + 4   # space above board for label
    SCORE_H   = font_tiny.get_height() + 6   # space below board for score
    ROOT_DOT_Y= CONTENT_Y + int(CONTENT_H*0.06)
    BOARDS_Y  = ROOT_DOT_Y + LABEL_H + 16    # boards row: root dot + label space + gap
    # Rejected row: below boards + score + gap
    REJ_Y     = BOARDS_Y + MINI_SIZE + SCORE_H + int(CONTENT_H*0.04)
    REJ_MINI  = max(40, MINI_SIZE//2)
    REJ_LABEL_H = font_tiny.get_height() + 4
    # Clamp rejected row so it doesn't exceed content area
    REJ_Y     = min(REJ_Y, CTRL_Y - REJ_MINI - REJ_LABEL_H - 10)

    # ── Slide animation ──
    START_BX  = SW//2 - BOARD_W//2
    START_BY  = SH//2 - BOARD_W//2

    # ── Control strip layout ──
    BTN_H = min(32, max(24, int(CTRL_H*0.36)))
    BTN_W = max(100, int(SW*0.088))
    gap   = 8
    # Slider: left side of ctrl strip
    SL_X = BX
    SL_Y = CTRL_Y + int(CTRL_H*0.30)
    SL_W = min(int(SW*0.17), BOARD_W)
    # Buttons: two rows on the right side
    BR1_Y = CTRL_Y + int(CTRL_H*0.12)                    # row 1
    BR2_Y = BR1_Y + BTN_H + gap                          # row 2

    r_restart  = pygame.Rect(SW-BTN_W-gap,       BR1_Y, BTN_W, BTN_H)
    r_step_tog = pygame.Rect(SW-BTN_W*2-gap*2,   BR1_Y, BTN_W, BTN_H)
    r_pause    = pygame.Rect(SW-BTN_W*3-gap*3,   BR1_Y, BTN_W, BTN_H)
    r_back     = pygame.Rect(SW-BTN_W-gap,        BR2_Y, BTN_W, BTN_H)
    r_next_move= pygame.Rect(SW-BTN_W*2-gap*2,   BR2_Y, BTN_W*2+gap, BTN_H)

    def make_game():
        g=checkers.Game(loop_mode=True,skip_graphics=True)
        bb=gamebot.Bot(g,BLUE,mid_eval='piece_and_board',end_eval='sum_of_dist',method='alpha_beta',depth=depth)
        br=gamebot.Bot(g,RED, mid_eval='piece_and_board',end_eval='sum_of_dist',method='alpha_beta',depth=depth)
        return g,bb,br

    game,bot_blue,bot_red=make_game()
    slider=Slider(SL_X,SL_Y,SL_W,0.1,3.0,0.8,"Delay")

    phase=PHASE_READY; phase_elapsed=0.0
    tree_nodes=[]; rejected_nodes=[]
    move_count=0; nodes_explored=0
    last_move_time=time.time()
    game_over=False; winner=None; paused=False
    step_mode=False; step_triggered=False
    phase4_elapsed=0.0; move_flash_timer=0.0
    step_mode_announce_t=0.0; exiting=False; exit_timer=0.0
    fade_surf=pygame.Surface((SW,SH)); fade_surf.fill((0,0,0))

    def get_bot(): return bot_blue if game.turn==BLUE else bot_red

    def do_step():
        nonlocal tree_nodes,rejected_nodes,nodes_explored,move_count,phase4_elapsed,move_flash_timer
        bot=get_bot()
        top,rej=bot.get_top_candidates(game.board,n=4)
        nodes_explored=bot._count_nodes; move_count+=1
        tree_nodes=[{
            'board':c['board_clone'],'score':c['score'],
            'chosen':i==0,'label':('★ CHOSEN' if i==0 else f'Option {i+1}'),
        } for i,c in enumerate(top)]
        rejected_nodes=rej
        phase4_elapsed=0.0; move_flash_timer=0.4

    while True:
        dt=clock.tick(60)/1000.0
        mp=pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type==QUIT: pygame.quit(); sys.exit()
            if event.type==KEYDOWN:
                if event.key==K_ESCAPE and not exiting: exiting=True; exit_timer=0.0
                if event.key==K_SPACE and phase==PHASE_GAMEPLAY and not step_mode: paused=not paused
                if event.key==K_RIGHT and phase==PHASE_GAMEPLAY and step_mode and not game_over: step_triggered=True
            if phase==PHASE_GAMEPLAY and not exiting:
                slider.handle_event(event)
                if event.type==MOUSEBUTTONDOWN and event.button==1:
                    if r_back.collidepoint(mp): exiting=True; exit_timer=0.0
                    if r_restart.collidepoint(mp):
                        game,bot_blue,bot_red=make_game()
                        tree_nodes=[];rejected_nodes=[];move_count=0;nodes_explored=0
                        last_move_time=time.time();game_over=False;winner=None;paused=False
                        phase4_elapsed=0.0;move_flash_timer=0.0
                    if r_pause.collidepoint(mp) and not step_mode: paused=not paused
                    if r_step_tog.collidepoint(mp):
                        step_mode=not step_mode; slider.disabled=step_mode; paused=False
                        if step_mode: step_mode_announce_t=1.5
                    if r_next_move.collidepoint(mp) and step_mode and not game_over: step_triggered=True

        phase_elapsed+=dt
        if   phase==PHASE_READY   and phase_elapsed>=1.0: phase=PHASE_SLIDE;    phase_elapsed=0.0
        elif phase==PHASE_SLIDE   and phase_elapsed>=0.6: phase=PHASE_CTRLSIN;  phase_elapsed=0.0
        elif phase==PHASE_CTRLSIN and phase_elapsed>=0.4: phase=PHASE_GAMEPLAY; phase_elapsed=0.0; last_move_time=time.time()

        if phase==PHASE_GAMEPLAY and not game_over and not exiting:
            if step_mode:
                if step_triggered:
                    do_step(); step_triggered=False
                    if game.endit: game_over=True; winner=game.winner or ("BLUE" if game.turn==RED else "RED")
            else:
                if not paused and time.time()-last_move_time>=slider.value:
                    do_step(); last_move_time=time.time()
                    if game.endit: game_over=True; winner=game.winner or ("BLUE" if game.turn==RED else "RED")

        phase4_elapsed=max(0.0,phase4_elapsed+dt)
        move_flash_timer=max(0.0,move_flash_timer-dt)
        step_mode_announce_t=max(0.0,step_mode_announce_t-dt)
        if exiting: exit_timer+=dt

        # Board animated position
        if phase==PHASE_READY:
            cur_bx,cur_by=START_BX,START_BY; panel_alpha=0; ctrl_alpha=0
        elif phase==PHASE_SLIDE:
            t_s=min(1.0,phase_elapsed/0.6); ease=1-(1-t_s)**3
            cur_bx=int(START_BX+(BX-START_BX)*ease); cur_by=int(START_BY+(BY-START_BY)*ease)
            panel_alpha=int(255*ease); ctrl_alpha=0
        elif phase==PHASE_CTRLSIN:
            cur_bx,cur_by=BX,BY; panel_alpha=255; ctrl_alpha=int(255*min(1.0,phase_elapsed/0.4))
        else:
            cur_bx,cur_by=BX,BY; panel_alpha=255; ctrl_alpha=255

        # ══ DRAW ══
        screen.fill(BG_DARK)

        # ── Top bar ──
        pygame.draw.rect(screen,(12,15,24),(0,0,SW,TOP_BAR_H))
        pygame.draw.line(screen,BORDER,(0,TOP_BAR_H),(SW,TOP_BAR_H),1)
        tc=ACCENT_BLUE if game.turn==BLUE else ACCENT_RED
        ts="BLUE's turn" if game.turn==BLUE else "RED's turn"
        if game_over: ts=f"{winner} WINS!"; tc=ACCENT_GOLD
        # Left: live game label
        tl=font_lg.render(f"LIVE GAME  ·  {ts}",True,tc)
        screen.blit(tl,(BX, TOP_BAR_H//2-tl.get_height()//2))
        # Center: stats
        stat_str=f"Move: {move_count}   Depth: {depth}   Nodes: {nodes_explored}"
        st=font_sm.render(stat_str,True,TEXT_DIM)
        screen.blit(st,(SW//2-st.get_width()//2, TOP_BAR_H//2-st.get_height()//2))

        # ── Divider between left and right panels ──
        pygame.draw.line(screen,BORDER,(DIVIDER_X,CONTENT_Y),(DIVIDER_X,CTRL_Y),1)

        # ── Ambient glow on board ──
        ambient_a=int(10+6*math.sin(pygame.time.get_ticks()*0.002))
        gs=pygame.Surface((BOARD_W+10,BOARD_W+10),pygame.SRCALPHA)
        pygame.draw.rect(gs,(*ACCENT_GOLD,ambient_a),(0,0,BOARD_W+10,BOARD_W+10),3,border_radius=5)
        screen.blit(gs,(cur_bx-5,cur_by-5))

        # Board
        pygame.draw.rect(screen,BG_CARD,(cur_bx-2,cur_by-2,BOARD_W+4,BOARD_W+4),border_radius=4)
        _draw_checkers_board(screen,game.board,cur_bx,cur_by,BOARD_W)

        if move_flash_timer>0:
            fa=int(160*(move_flash_timer/0.4))
            fs=pygame.Surface((BOARD_W,BOARD_W),pygame.SRCALPHA); fs.fill((50,220,120,fa))
            screen.blit(fs,(cur_bx,cur_by))

        pygame.draw.rect(screen,ACCENT_GOLD,(cur_bx-2,cur_by-2,BOARD_W+4,BOARD_W+4),2,border_radius=4)

        # Game over overlay
        if game_over:
            ov=pygame.Surface((BOARD_W,BOARD_W)); ov.fill((0,0,0)); ov.set_alpha(170)
            screen.blit(ov,(cur_bx,cur_by))
            wc=ACCENT_BLUE if winner=="BLUE" else ACCENT_RED
            wt=font_xl.render(f"{winner} WINS!",True,wc)
            screen.blit(wt,(cur_bx+BOARD_W//2-wt.get_width()//2,cur_by+BOARD_W//2-20))
            ht=font_sm.render("Press ↺ RESTART",True,TEXT_DIM)
            screen.blit(ht,(cur_bx+BOARD_W//2-ht.get_width()//2,cur_by+BOARD_W//2+16))

        if paused and not game_over and phase==PHASE_GAMEPLAY:
            ov=pygame.Surface((BOARD_W,BOARD_W)); ov.fill((0,0,0)); ov.set_alpha(140)
            screen.blit(ov,(cur_bx,cur_by))
            pt=font_xl.render("PAUSED",True,ACCENT_GOLD)
            screen.blit(pt,(cur_bx+BOARD_W//2-pt.get_width()//2,cur_by+BOARD_W//2-pt.get_height()//2))

        # Phase READY intro overlay
        if phase==PHASE_READY:
            t_ready=min(1.0,phase_elapsed/0.5); title_a=int(255*t_ready)
            for surf,ry in [
                (font_xl.render("AI  vs  AI",True,ACCENT_GOLD), cur_by-font_xl.get_height()-10),
                (font_sm.render("Initializing game tree...",True,TEXT_DIM), cur_by+BOARD_W+8)
            ]:
                ss=pygame.Surface((surf.get_width(),surf.get_height()),pygame.SRCALPHA)
                ss.blit(surf,(0,0)); ss.set_alpha(title_a)
                screen.blit(ss,(SW//2-surf.get_width()//2, max(0,ry)))

        # ── Tree panel ──
        if panel_alpha>0:
            # Header (clip if too wide)
            hdr_txt="DECISION TREE  —  Top 4 Candidate Moves"
            th=font_xl.render(hdr_txt,True,ACCENT_GOLD)
            if th.get_width()>TREE_W:
                th=font_lg.render("DECISION TREE  —  Top 4",True,ACCENT_GOLD)
            ths=pygame.Surface((th.get_width(),th.get_height()),pygame.SRCALPHA)
            ths.blit(th,(0,0)); ths.set_alpha(panel_alpha)
            # Centre header in tree panel
            hdr_x=TREE_X+(TREE_W-th.get_width())//2
            hdr_y=CONTENT_Y+(TOP_BAR_H//2)-th.get_height()//2 - TOP_BAR_H + 4
            hdr_y=max(CONTENT_Y+2, hdr_y)
            screen.blit(ths,(hdr_x, CONTENT_Y+4))

            if tree_nodes:
                total_w=4*MINI_SIZE+3*MINI_GAP
                root_cx=TREE_X+total_w//2

                # Root dot with label below it
                pygame.draw.circle(screen,ACCENT_GOLD,(root_cx,ROOT_DOT_Y),5)
                rl=font_tiny.render("current position",True,TEXT_DIM)
                screen.blit(rl,(root_cx-rl.get_width()//2, ROOT_DOT_Y+8))

                for i,node in enumerate(tree_nodes):
                    bx2=TREE_X+i*(MINI_SIZE+MINI_GAP)
                    bc2=bx2+MINI_SIZE//2

                    delay_i=i*0.08
                    t_i=min(1.0,max(0.0,phase4_elapsed-delay_i)/0.35)
                    ease_i=1-(1-t_i)**2
                    alpha_i=int(255*ease_i)
                    y_off_i=int(18*(1.0-ease_i))

                    if alpha_i<=0: continue

                    # Connector line root→board
                    ls=pygame.Surface((SW,SH),pygame.SRCALPHA)
                    lc=CHOSEN_BD if node['chosen'] else BORDER
                    pygame.draw.line(ls,(*lc,alpha_i),(root_cx,ROOT_DOT_Y+6),(bc2,BOARDS_Y-LABEL_H-2),1)
                    screen.blit(ls,(0,0))

                    # Mini board drawn onto its own surface (MINI_SIZE + label above + score below)
                    surf_h=LABEL_H+MINI_SIZE+SCORE_H+y_off_i+4
                    surf_w=MINI_SIZE+4
                    tmp=pygame.Surface((surf_w,surf_h),pygame.SRCALPHA)
                    sv=node['score']
                    if sv==float('inf'): sv=999
                    # Draw: label at top of surf, board below label, score below board
                    _draw_mini_board(tmp,node['board'],2,LABEL_H+y_off_i,MINI_SIZE,font_tiny,
                                     chosen=node['chosen'],label=node['label'],score=sv)
                    tmp.set_alpha(alpha_i)
                    screen.blit(tmp,(bx2-2, BOARDS_Y-LABEL_H))

                    # Pulsing chosen border
                    if node['chosen'] and alpha_i==255:
                        pa=int(100+80*math.sin(pygame.time.get_ticks()*0.003))
                        pb=pygame.Surface((MINI_SIZE+10,MINI_SIZE+10),pygame.SRCALPHA)
                        pygame.draw.rect(pb,(*CHOSEN_BD,pa),(0,0,MINI_SIZE+10,MINI_SIZE+10),2,border_radius=5)
                        screen.blit(pb,(bx2-5, BOARDS_Y-5))

                # Rejected section
                rej_elapsed=phase4_elapsed-0.6
                rej_alpha=int(255*min(1.0,max(0.0,rej_elapsed/0.3)))
                if rej_alpha>0 and rejected_nodes and REJ_Y+REJ_MINI < CTRL_Y-4:
                    pygame.draw.line(screen,REJECTED_BD,(TREE_X,REJ_Y-1),(TREE_X+TREE_W,REJ_Y-1),1)
                    rl2=font_tiny.render(f"α-β PRUNED: {len(rejected_nodes)} moves eliminated",True,REJECTED_BD)
                    rl2s=pygame.Surface((rl2.get_width(),rl2.get_height()),pygame.SRCALPHA)
                    rl2s.blit(rl2,(0,0)); rl2s.set_alpha(rej_alpha)
                    screen.blit(rl2s,(TREE_X, REJ_Y-rl2.get_height()-4))
                    for i in range(min(8,len(rejected_nodes))):
                        rx=TREE_X+i*(REJ_MINI+MINI_GAP)
                        if rx+REJ_MINI>SW-10: break
                        rtmp=pygame.Surface((REJ_MINI+4,REJ_MINI+4),pygame.SRCALPHA)
                        _draw_mini_board(rtmp,None,2,2,REJ_MINI,font_tiny,rejected=True)
                        rtmp.set_alpha(rej_alpha)
                        screen.blit(rtmp,(rx-2,REJ_Y))
            else:
                # No moves yet
                wt=font_lg.render("Waiting for first AI move...",True,TEXT_DIM)
                wts=pygame.Surface((wt.get_width(),wt.get_height()),pygame.SRCALPHA)
                wts.blit(wt,(0,0)); wts.set_alpha(panel_alpha)
                screen.blit(wts,(TREE_X+20, BOARDS_Y+MINI_SIZE//2))

        # ── Control strip ──
        pygame.draw.rect(screen,(10,13,22),(0,CTRL_Y,SW,CTRL_H))
        pygame.draw.line(screen,BORDER,(0,CTRL_Y),(SW,CTRL_Y),1)

        if ctrl_alpha>0:
            slider.disabled=step_mode
            slider.draw(screen,font_tiny)

            # Hint text below slider
            hint=font_tiny.render("SPACE=pause  →=step(step mode)",True,TEXT_DIM)
            screen.blit(hint,(SL_X, SL_Y+slider.rect.h+4))

            _btn(screen,r_restart,"↺ RESTART",  r_restart.collidepoint(mp),  font_sm,ACCENT_BLUE)
            _btn(screen,r_back,   "← MENU",     r_back.collidepoint(mp),     font_sm,TEXT_DIM)
            step_lbl="AUTO PLAY" if step_mode else "STEP MODE"
            _btn(screen,r_step_tog,step_lbl,     r_step_tog.collidepoint(mp),font_sm,ACCENT_GOLD)

            if step_mode:
                _btn(screen,r_next_move,"▶  NEXT MOVE",r_next_move.collidepoint(mp),font_sm,ACCENT_GREEN)
            else:
                pl="▶ RESUME" if paused else "⏸ PAUSE"
                _btn(screen,r_pause,pl,r_pause.collidepoint(mp),font_sm,ACCENT_GOLD)

            if ctrl_alpha<255:
                ov=pygame.Surface((SW,SH)); ov.fill(BG_DARK); ov.set_alpha(255-ctrl_alpha)
                screen.blit(ov,(0,0))

        # Step mode announce
        if step_mode_announce_t>0:
            ann_a=min(255,int(255*step_mode_announce_t))
            ann=pygame.Surface((BOARD_W,BOARD_W)); ann.fill((0,0,0)); ann.set_alpha(int(ann_a*0.7))
            screen.blit(ann,(cur_bx,cur_by))
            for surf,oy in [
                (font_xl.render("STEP MODE ACTIVE",True,ACCENT_GOLD),-20),
                (font_sm.render("Click NEXT MOVE or press →",True,TEXT_WHITE),12)
            ]:
                ss=pygame.Surface((surf.get_width(),surf.get_height()),pygame.SRCALPHA)
                ss.blit(surf,(0,0)); ss.set_alpha(ann_a)
                screen.blit(ss,(cur_bx+BOARD_W//2-surf.get_width()//2, cur_by+BOARD_W//2+oy))

        # Exit fade
        if exiting:
            fade_surf.set_alpha(int(255*min(1.0,exit_timer/0.3)))
            screen.blit(fade_surf,(0,0))
            if exit_timer>=0.3: return

        pygame.display.flip()