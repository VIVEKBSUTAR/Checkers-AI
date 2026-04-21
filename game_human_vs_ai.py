import pygame
import sys
import math
import time
from pygame.locals import *
import checkers
import gamebot

WHITE=(255,255,255); BLUE=(0,0,255); RED=(255,0,0); BLACK=(0,0,0); GOLD=(255,215,0)
BG_DARK=(10,12,20); ACCENT_BLUE=(64,156,255); ACCENT_RED=(255,75,75); ACCENT_GOLD=(255,200,50)
ACCENT_GREEN=(50,220,120); TEXT_WHITE=(230,235,255); TEXT_DIM=(100,110,140)
PANEL_BG=(14,18,30); BORDER=(35,45,70)
PIECE_BLUE=(30,80,220); PIECE_BLUE_HI=(100,150,255)
PIECE_RED=(200,30,30);  PIECE_RED_HI=(255,100,80)

pygame.font.init()


def _draw_piece(surface, color, cx, cy, r, king=False, selected=False, pulse=0.0):
    fill   = PIECE_BLUE    if color==BLUE else PIECE_RED
    hi_col = PIECE_BLUE_HI if color==BLUE else PIECE_RED_HI
    if selected:
        ring_r=r+int(3+3*math.sin(pulse))
        ring_a=int(140+80*math.sin(pulse))
        rs=pygame.Surface((ring_r*2+4,ring_r*2+4),pygame.SRCALPHA)
        pygame.draw.circle(rs,(*ACCENT_GOLD,ring_a),(ring_r+2,ring_r+2),ring_r,2)
        surface.blit(rs,(cx-ring_r-2,cy-ring_r-2))
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


def _draw_board(surface, game, bx, by, board_size, pulse):
    sq=board_size//8
    # Draw squares
    for row in range(8):
        for col in range(8):
            c=(200,160,110) if (row+col)%2==0 else (80,50,28)
            pygame.draw.rect(surface,c,(bx+col*sq,by+row*sq,sq,sq))

    # Selected piece glow (drawn before pieces, on top of squares)
    if game.selected_piece is not None:
        sp=game.selected_piece
        glow_cx=bx+sp[0]*sq+sq//2; glow_cy=by+sp[1]*sq+sq//2
        glow_r=sq//2+int(4*math.sin(pulse))
        glow_a=int(80+40*math.sin(pulse))
        gs=pygame.Surface((glow_r*2+10,glow_r*2+10),pygame.SRCALPHA)
        pygame.draw.circle(gs,(*ACCENT_GOLD,glow_a),(glow_r+5,glow_r+5),glow_r,4)
        surface.blit(gs,(glow_cx-glow_r-5,glow_cy-glow_r-5))

        # Legal move dots
        for mv in game.board.legal_moves(sp[0],sp[1],game.hop):
            dot_cx=bx+mv[0]*sq+sq//2; dot_cy=by+mv[1]*sq+sq//2
            dot_s=pygame.Surface((sq,sq),pygame.SRCALPHA)
            pygame.draw.circle(dot_s,(*ACCENT_BLUE,180),(sq//2,sq//2),max(6,sq//5))
            surface.blit(dot_s,(bx+mv[0]*sq,by+mv[1]*sq))

    # Pieces
    r=max(8,sq//2-4)
    for row in range(8):
        for col in range(8):
            occ=game.board.matrix[col][row].occupant
            if occ is None: continue
            pcx=bx+col*sq+sq//2; pcy=by+row*sq+sq//2
            is_sel=game.selected_piece==(col,row)
            _draw_piece(surface,occ.color,pcx,pcy,r,king=occ.king,selected=is_sel,pulse=pulse)


def _handle_human_event(game, event, bx, by, board_size):
    if event.type!=MOUSEBUTTONDOWN or event.button!=1: return
    sq=board_size//8
    bc=(event.pos[0]-bx)//sq; br=(event.pos[1]-by)//sq
    if not (0<=bc<=7 and 0<=br<=7): return
    mpos=(bc,br)
    if not game.hop:
        if (game.board.location(mpos[0],mpos[1]).occupant is not None and
                game.board.location(mpos[0],mpos[1]).occupant.color==game.turn):
            game.selected_piece=mpos
        elif game.selected_piece is not None and mpos in game.board.legal_moves(game.selected_piece[0],game.selected_piece[1]):
            game.board.move_piece(game.selected_piece[0],game.selected_piece[1],mpos[0],mpos[1])
            if mpos not in game.board.adjacent(game.selected_piece[0],game.selected_piece[1]):
                game.board.remove_piece(
                    game.selected_piece[0]+(mpos[0]-game.selected_piece[0])//2,
                    game.selected_piece[1]+(mpos[1]-game.selected_piece[1])//2)
                game.hop=True; game.selected_piece=mpos
            else: game.end_turn()
    if game.hop:
        if game.selected_piece is not None and mpos in game.board.legal_moves(game.selected_piece[0],game.selected_piece[1],True):
            game.board.move_piece(game.selected_piece[0],game.selected_piece[1],mpos[0],mpos[1])
            game.board.remove_piece(
                game.selected_piece[0]+(mpos[0]-game.selected_piece[0])//2,
                game.selected_piece[1]+(mpos[1]-game.selected_piece[1])//2)
        if game.board.legal_moves(mpos[0],mpos[1],True)==[]: game.end_turn()
        else: game.selected_piece=mpos


def _count_pieces(board):
    blue=red=0
    for i in range(8):
        for j in range(8):
            occ=board.matrix[i][j].occupant
            if occ:
                if occ.color==BLUE: blue+=1
                else: red+=1
    return blue,red


def _draw_piece_bar(surface,x,y,w,h,count,max_count,color,fonts):
    pygame.draw.rect(surface,(30,30,50),(x,y,w,h),border_radius=4)
    fw=int(w*count/max(max_count,1))
    if fw>0: pygame.draw.rect(surface,color,(x,y,fw,h),border_radius=4)
    pygame.draw.rect(surface,BORDER,(x,y,w,h),1,border_radius=4)
    lc=ACCENT_BLUE if color==PIECE_BLUE else ACCENT_RED
    t=fonts['small'].render(f"{count}/{max_count}",True,lc)
    surface.blit(t,(x+w+8,y+(h-t.get_height())//2))


def run_human_vs_ai(depth):
    pygame.init()
    info=pygame.display.Info()
    SW,SH=info.current_w,info.current_h
    screen=pygame.display.set_mode((SW,SH),pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
    pygame.display.set_caption(f"Checkers AI — Player vs AI  ·  Depth {depth}")
    clock=pygame.time.Clock()

    scale=min(SW/1280,SH/720)
    sz=lambda n: max(10,int(n*scale))
    try:
        font_xl=pygame.font.SysFont('couriernew',sz(26),bold=True)
        font_lg=pygame.font.SysFont('couriernew',sz(18),bold=True)
        font_sm=pygame.font.SysFont('couriernew',sz(13))
    except:
        font_xl=pygame.font.Font(None,sz(32)); font_lg=pygame.font.Font(None,sz(22))
        font_sm=pygame.font.Font(None,sz(17))
    fonts={'xl':font_xl,'lg':font_lg,'sm':font_sm,'small':font_sm}

    diff_names={1:'EASY',2:'MEDIUM',3:'HARD',5:'EXPERT'}
    diff_label=diff_names.get(depth,f'DEPTH {depth}')

    BOARD_SIZE=min(int(SW*0.64),int(SH*0.90)); BOARD_SIZE=(BOARD_SIZE//8)*8
    BX=int(SW*0.02); BY=(SH-BOARD_SIZE)//2
    PANEL_X=BX+BOARD_SIZE+int(SW*0.02)
    PANEL_W=SW-PANEL_X-int(SW*0.01)
    PAD=max(16,int(PANEL_W*0.06))

    def make_game():
        g=checkers.Game(loop_mode=True,skip_graphics=True)
        b=gamebot.Bot(g,RED,mid_eval='piece_and_board',end_eval='sum_of_dist',method='alpha_beta',depth=depth)
        return g,b

    game,bot=make_game()
    nodes_explored=0; move_count=0; winner=None; game_over=False
    status_msg="YOUR TURN — Click a piece"
    ai_flash_timer=0.0; INIT_PIECES=12; pulse=0.0

    btn_h=max(34,int(SH*0.048)); btn_w=PANEL_W-2*PAD
    back_rect   =pygame.Rect(PANEL_X+PAD,SH-btn_h-12,btn_w,btn_h)
    restart_rect=pygame.Rect(PANEL_X+PAD,SH-btn_h*2-24,btn_w,btn_h)

    # Fade state
    intro_alpha=255.0
    exiting=False; exit_timer=0.0
    fade_surf=pygame.Surface((SW,SH)); fade_surf.fill((0,0,0))

    while True:
        dt=clock.tick(60)/1000.0
        pulse+=dt*3.0; mp=pygame.mouse.get_pos()
        ai_flash_timer=max(0,ai_flash_timer-dt)

        for event in pygame.event.get():
            if event.type==QUIT: pygame.quit(); sys.exit()
            if event.type==KEYDOWN and event.key==K_ESCAPE and not exiting:
                exiting=True; exit_timer=0.0
            if not game_over and game.turn==BLUE and not exiting:
                _handle_human_event(game,event,BX,BY,BOARD_SIZE)
            if event.type==MOUSEBUTTONDOWN and event.button==1 and not exiting:
                if back_rect.collidepoint(mp): exiting=True; exit_timer=0.0
                if restart_rect.collidepoint(mp):
                    game,bot=make_game(); nodes_explored=0; move_count=0
                    winner=None; game_over=False; status_msg="YOUR TURN — Click a piece"

        if not game_over and game.turn==RED and not exiting:
            # Show thinking frame first
            screen.fill(BG_DARK)
            _draw_board(screen,game,BX,BY,BOARD_SIZE,pulse)
            pygame.draw.rect(screen,ACCENT_GOLD,(BX-3,BY-3,BOARD_SIZE+6,BOARD_SIZE+6),2,border_radius=4)
            # Sidebar
            pygame.draw.rect(screen,PANEL_BG,(PANEL_X,0,PANEL_W,SH))
            pygame.draw.line(screen,BORDER,(PANEL_X,0),(PANEL_X,SH),2)
            think_t=font_lg.render("AI THINKING...",True,ACCENT_RED)
            screen.blit(think_t,(PANEL_X+PAD,SH//2-20))
            pygame.display.flip()

            status_msg="AI THINKING..."
            nodes_explored=bot.step(game.board,True) or 0
            move_count+=1
            status_msg=f"AI moved  |  Nodes: {nodes_explored}"
            ai_flash_timer=0.4

        if not game_over and game.endit:
            game_over=True
            winner="YOU (BLUE)" if game.turn==RED else "AI (RED)"

        # ── Draw ──
        screen.fill(BG_DARK)

        if ai_flash_timer>0:
            a=int(180*(ai_flash_timer/0.4))
            fs=pygame.Surface((BOARD_SIZE,BOARD_SIZE),pygame.SRCALPHA); fs.fill((50,220,120,a))
            screen.blit(fs,(BX,BY))

        _draw_board(screen,game,BX,BY,BOARD_SIZE,pulse)
        pygame.draw.rect(screen,ACCENT_GOLD,(BX-3,BY-3,BOARD_SIZE+6,BOARD_SIZE+6),2,border_radius=4)

        # Sidebar
        pygame.draw.rect(screen,PANEL_BG,(PANEL_X,0,PANEL_W,SH))
        pygame.draw.line(screen,BORDER,(PANEL_X,0),(PANEL_X,SH),2)
        px,py=PANEL_X+PAD,20

        screen.blit(font_lg.render("CHECKERS AI",True,ACCENT_BLUE),(px,py)); py+=font_lg.get_height()+6
        dc=ACCENT_GOLD if diff_label in ('HARD','EXPERT') else ACCENT_BLUE
        screen.blit(font_sm.render(f"[ {diff_label} ]",True,dc),(px,py)); py+=22
        pygame.draw.line(screen,BORDER,(px,py),(px+PANEL_W-PAD*2,py)); py+=14

        tc=ACCENT_BLUE if game.turn==BLUE else ACCENT_RED
        tt="YOUR TURN" if game.turn==BLUE else "AI TURN"
        if game_over: tt="GAME OVER"; tc=ACCENT_GOLD
        screen.blit(font_lg.render(tt,True,tc),(px,py)); py+=28
        pygame.draw.line(screen,BORDER,(px,py),(px+PANEL_W-PAD*2,py)); py+=14

        screen.blit(font_sm.render("STATUS:",True,TEXT_DIM),(px,py)); py+=18
        words=status_msg.split(); line=""
        for w in words:
            test=line+w+" "
            if font_sm.size(test)[0]>PANEL_W-PAD*2:
                screen.blit(font_sm.render(line,True,TEXT_WHITE),(px,py)); py+=16; line=w+" "
            else: line=test
        if line: screen.blit(font_sm.render(line,True,TEXT_WHITE),(px,py)); py+=22
        pygame.draw.line(screen,BORDER,(px,py),(px+PANEL_W-PAD*2,py)); py+=14

        screen.blit(font_sm.render("STATS:",True,TEXT_DIM),(px,py)); py+=18
        for lbl in [f"Move #: {move_count}",f"Nodes: {nodes_explored}",f"Depth: {depth}","Method: α-β Pruning"]:
            screen.blit(font_sm.render(lbl,True,TEXT_WHITE),(px,py)); py+=16
        py+=8
        pygame.draw.line(screen,BORDER,(px,py),(px+PANEL_W-PAD*2,py)); py+=14

        blue_c,red_c=_count_pieces(game.board)
        screen.blit(font_sm.render("PIECES:",True,TEXT_DIM),(px,py)); py+=18
        screen.blit(font_sm.render("BLUE (You)",True,ACCENT_BLUE),(px,py)); py+=16
        _draw_piece_bar(screen,px,py,max(80,PANEL_W-PAD*2-50),14,blue_c,INIT_PIECES,PIECE_BLUE,fonts); py+=26
        screen.blit(font_sm.render("RED (AI)",True,ACCENT_RED),(px,py)); py+=16
        _draw_piece_bar(screen,px,py,max(80,PANEL_W-PAD*2-50),14,red_c,INIT_PIECES,PIECE_RED,fonts); py+=26
        pygame.draw.line(screen,BORDER,(px,py),(px+PANEL_W-PAD*2,py)); py+=14
        screen.blit(font_sm.render("YOU  = BLUE ●",True,ACCENT_BLUE),(px,py)); py+=16
        screen.blit(font_sm.render("AI   = RED  ●",True,ACCENT_RED),(px,py)); py+=20

        if game_over and winner:
            pygame.draw.line(screen,BORDER,(px,py),(px+PANEL_W-PAD*2,py)); py+=14
            wc=ACCENT_BLUE if "BLUE" in winner else ACCENT_RED
            screen.blit(font_xl.render("WINNER:",True,ACCENT_GOLD),(px,py)); py+=32
            screen.blit(font_lg.render(winner,True,wc),(px,py))

        for r,lbl in [(restart_rect,"↺ RESTART"),(back_rect,"← MAIN MENU")]:
            hov=r.collidepoint(mp)
            pygame.draw.rect(screen,PANEL_BG,r,border_radius=6)
            pygame.draw.rect(screen,ACCENT_BLUE if hov else BORDER,r,2,border_radius=6)
            bt=font_sm.render(lbl,True,TEXT_WHITE)
            screen.blit(bt,(r.centerx-bt.get_width()//2,r.centery-bt.get_height()//2))

        # Fade-in
        if intro_alpha>0:
            fade_surf.set_alpha(int(intro_alpha))
            screen.blit(fade_surf,(0,0))
            intro_alpha=max(0.0,intro_alpha-dt*637)

        # Exit fade-out
        if exiting:
            exit_timer+=dt
            fade_surf.set_alpha(int(255*min(1.0,exit_timer/0.3)))
            screen.blit(fade_surf,(0,0))
            if exit_timer>=0.3: return

        pygame.display.flip()