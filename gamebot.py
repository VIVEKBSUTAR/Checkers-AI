import pygame
import sys
from pygame.locals import *
import random
from copy import deepcopy
import math

pygame.font.init()

WHITE = (255, 255, 255)
BLUE  = (0,   0, 255)
RED   = (255, 0,   0)
BLACK = (0,   0,   0)
GOLD  = (255, 215,  0)
HIGH  = (160, 190, 255)

NORTHWEST = "northwest"
NORTHEAST = "northeast"
SOUTHWEST = "southwest"
SOUTHEAST = "southeast"

CENTER_SQUARES = {(3,3),(4,3),(3,4),(4,4)}
NEAR_CENTER    = {(2,2),(5,2),(2,5),(5,5),(3,2),(4,2),(2,3),(5,3),(2,4),(5,4),(3,5),(4,5)}

class Bot:
    def __init__(self, game, color, method='random', mid_eval=None, end_eval=None, depth=1):
        self.method = method
        if   mid_eval == 'piece2val':          self._mid_eval = self._piece2val
        elif mid_eval == 'piece_and_board':    self._mid_eval = self._piece_and_board2val
        elif mid_eval == 'piece_and_row':      self._mid_eval = self._piece_and_row2val
        elif mid_eval == 'piece_and_board_pov':self._mid_eval = self._piece_and_board_pov2val
        else:                                  self._mid_eval = self._piece_and_board2val
        if   end_eval == 'sum_of_dist':        self._end_eval = self._sum_of_dist
        elif end_eval == 'farthest_piece':     self._end_eval = self._farthest_piece
        else:                                  self._end_eval = None
        self.depth = depth
        self.game  = game
        self.color = color
        self.eval_color = color
        self.adversary_color = RED if color == BLUE else BLUE
        self._current_eval = self._mid_eval
        self._end_eval_time = False
        self._count_nodes   = 0

    def _is_endgame(self, board):
        total = sum(1 for i in range(8) for j in range(8) if board.location(i,j).occupant is not None)
        return total < 8

    def _all_kings(self, board):
        for i in range(8):
            for j in range(8):
                occ = board.location(i,j).occupant
                if occ is not None and not occ.king:
                    return False
        return True

    def step(self, board, return_count_nodes=False):
        self._count_nodes = 0
        if self._end_eval is not None and not self._end_eval_time:
            if self._is_endgame(board):
                print('END EVAL is on')
                self._end_eval_time = True
                self._current_eval  = self._end_eval
        if   self.method == 'random':     self._random_step(board)
        elif self.method == 'minmax':     self._minmax_step(board)
        elif self.method == 'alpha_beta': self._alpha_beta_step(board)
        if return_count_nodes: return self._count_nodes

    def get_top_candidates(self, board, n=4):
        self._count_nodes = 0
        if self._end_eval is not None and not self._end_eval_time:
            if self._is_endgame(board):
                self._end_eval_time = True
                self._current_eval  = self._end_eval
        candidates = []
        for pos in self._generate_move(board):
            for action in pos[2]:
                bc = deepcopy(board)
                self.color, self.adversary_color = self.adversary_color, self.color
                self.game.turn = self.color
                self._action_on_board(bc, pos, action)
                self._count_nodes += 1
                if self._check_for_endgame(bc):
                    score = float('inf')
                else:
                    if self.method == 'alpha_beta':
                        _, _, score = self._alpha_beta(max(0,self.depth-2), bc, 'min', -float('inf'), float('inf'))
                    else:
                        _, _, score = self._minmax(max(0,self.depth-2), bc, 'min')
                    if score is None: score = 0
                self.color, self.adversary_color = self.adversary_color, self.color
                self.game.turn = self.color
                candidates.append({'pos':(pos[0],pos[1]),'action':action,'score':score,'board_clone':bc,'rejected':False})
        candidates.sort(key=lambda c: c['score'] if c['score'] != float('inf') else 1e9, reverse=True)
        for i,c in enumerate(candidates): c['rejected'] = i >= n
        if candidates:
            best = candidates[0]
            self._action(best['pos'], best['action'], board)
        return candidates[:n], candidates[n:]

    def _action(self, current_pos, final_pos, board):
        if current_pos is None:
            self.game.end_turn(); return
        if self.game.hop == False:
            if board.location(final_pos[0],final_pos[1]).occupant is not None and board.location(final_pos[0],final_pos[1]).occupant.color == self.game.turn:
                current_pos = final_pos
            elif current_pos is not None and final_pos in board.legal_moves(current_pos[0],current_pos[1]):
                board.move_piece(current_pos[0],current_pos[1],final_pos[0],final_pos[1])
                if final_pos not in board.adjacent(current_pos[0],current_pos[1]):
                    board.remove_piece(current_pos[0]+(final_pos[0]-current_pos[0])//2, current_pos[1]+(final_pos[1]-current_pos[1])//2)
                    self.game.hop = True
                    current_pos = final_pos
                    final_pos   = board.legal_moves(current_pos[0],current_pos[1],True)
                    if final_pos: self._action(current_pos, final_pos[0], board)
                    self.game.end_turn()
        if self.game.hop == True:
            if current_pos is not None and final_pos in board.legal_moves(current_pos[0],current_pos[1],self.game.hop):
                board.move_piece(current_pos[0],current_pos[1],final_pos[0],final_pos[1])
                board.remove_piece(current_pos[0]+(final_pos[0]-current_pos[0])//2, current_pos[1]+(final_pos[1]-current_pos[1])//2)
            if board.legal_moves(final_pos[0],final_pos[1],self.game.hop) == []:
                self.game.end_turn()
            else:
                current_pos = final_pos
                final_pos   = board.legal_moves(current_pos[0],current_pos[1],True)
                if final_pos: self._action(current_pos, final_pos[0], board)
                self.game.end_turn()
        if self.game.hop != True:
            self.game.turn = self.adversary_color

    def _action_on_board(self, board, current_pos, final_pos, hop=False):
        if not hop:
            if board.location(final_pos[0],final_pos[1]).occupant is not None and board.location(final_pos[0],final_pos[1]).occupant.color == self.game.turn:
                current_pos = final_pos
            elif current_pos is not None and final_pos in board.legal_moves(current_pos[0],current_pos[1]):
                board.move_piece(current_pos[0],current_pos[1],final_pos[0],final_pos[1])
                if final_pos not in board.adjacent(current_pos[0],current_pos[1]):
                    board.remove_piece(current_pos[0]+(final_pos[0]-current_pos[0])//2, current_pos[1]+(final_pos[1]-current_pos[1])//2)
                    hop = True; current_pos = final_pos
                    final_pos = board.legal_moves(current_pos[0],current_pos[1],True)
                    if final_pos: self._action_on_board(board, current_pos, final_pos[0], hop=True)
        else:
            if current_pos is not None and final_pos in board.legal_moves(current_pos[0],current_pos[1],hop):
                board.move_piece(current_pos[0],current_pos[1],final_pos[0],final_pos[1])
                board.remove_piece(current_pos[0]+(final_pos[0]-current_pos[0])//2, current_pos[1]+(final_pos[1]-current_pos[1])//2)
            if board.legal_moves(final_pos[0],final_pos[1],self.game.hop) == []: return
            else:
                current_pos = final_pos
                final_pos   = board.legal_moves(current_pos[0],current_pos[1],True)
                if final_pos: self._action_on_board(board, current_pos, final_pos[0], hop=True)

    def _generate_move(self, board):
        for i in range(8):
            for j in range(8):
                moves = board.legal_moves(i,j,self.game.hop)
                if moves and board.location(i,j).occupant is not None and board.location(i,j).occupant.color == self.game.turn:
                    yield (i,j,moves)

    def _generate_all_possible_moves(self, board):
        return [(i,j,board.legal_moves(i,j,self.game.hop))
                for i in range(8) for j in range(8)
                if board.legal_moves(i,j,self.game.hop) and board.location(i,j).occupant is not None and board.location(i,j).occupant.color == self.game.turn]

    def _random_step(self, board):
        pm = self._generate_all_possible_moves(board)
        if not pm: self.game.end_turn(); return
        m = random.choice(pm); self._action(m, random.choice(m[2]), board)

    def _minmax_step(self, board):
        p,a,_ = self._minmax(self.depth-1, board, 'max'); self._action(p,a,board)

    def _alpha_beta_step(self, board):
        p,a,_ = self._alpha_beta(self.depth-1, board, 'max', -float('inf'), float('inf')); self._action(p,a,board)

    def _minmax(self, depth, board, fn):
        if depth == 0:
            if fn == 'max':
                bv,bp,ba = -float('inf'),None,None
                for pos in self._generate_move(board):
                    for act in pos[2]:
                        bc=deepcopy(board); self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        self._action_on_board(bc,pos,act); self._count_nodes+=1; v=self._current_eval(bc)
                        self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        if v>bv or (v==bv and random.random()<=0.5): bv,bp,ba=v,pos,(act[0],act[1])
                        if v==-float('inf') and bp is None: bp,ba=(pos[0],pos[1]),(act[0],act[1])
                return bp,ba,bv
            else:
                bv,bp,ba = float('inf'),None,None
                for pos in self._generate_move(board):
                    for act in pos[2]:
                        bc=deepcopy(board); self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        self._count_nodes+=1; self._action_on_board(bc,pos,act); v=self._current_eval(bc)
                        self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        if v<bv or (v==bv and random.random()<=0.5): bv,bp,ba=v,pos,act
                        if v==float('inf') and bp is None: bp,ba=(pos[0],pos[1]),(act[0],act[1])
                return bp,ba,bv
        else:
            if fn == 'max':
                bv,bp,ba = -float('inf'),None,None
                for pos in self._generate_move(board):
                    for act in pos[2]:
                        bc=deepcopy(board); self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        self._action_on_board(bc,pos,act); self._count_nodes+=1
                        v = float('inf') if self._check_for_endgame(bc) else self._minmax(depth-1,bc,'min')[2]
                        self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        if v is None: continue
                        if v>bv or (v==bv and random.random()<=0.5): bv,bp,ba=v,pos,act
                        if v==-float('inf') and bp is None: bp,ba=(pos[0],pos[1]),(act[0],act[1])
                return bp,ba,bv
            else:
                bv,bp,ba = float('inf'),None,None
                for pos in self._generate_move(board):
                    for act in pos[2]:
                        bc=deepcopy(board); self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        self._count_nodes+=1; self._action_on_board(bc,pos,act)
                        v = -float('inf') if self._check_for_endgame(bc) else self._minmax(depth-1,bc,'max')[2]
                        self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        if v is None: continue
                        if v<bv or (v==bv and random.random()<=0.5): bv,bp,ba=v,(pos[0],pos[1]),(act[0],act[1])
                        if v==float('inf') and bp is None: bp,ba=(pos[0],pos[1]),(act[0],act[1])
                return bp,ba,bv

    def _alpha_beta(self, depth, board, fn, alpha, beta):
        if depth == 0:
            if fn == 'max':
                bv,bp,ba = -float('inf'),None,None
                for pos in self._generate_move(board):
                    for act in pos[2]:
                        bc=deepcopy(board); self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        self._count_nodes+=1; self._action_on_board(bc,pos,act); v=self._current_eval(bc)
                        self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        if v>bv or (v==bv and random.random()<=0.5): bv,bp,ba=v,pos,(act[0],act[1])
                        if v==-float('inf') and bp is None: bp,ba=(pos[0],pos[1]),(act[0],act[1])
                        alpha=max(alpha,bv)
                        if beta<alpha: break
                    if beta<alpha: break
                return bp,ba,bv
            else:
                bv,bp,ba = float('inf'),None,None
                for pos in self._generate_move(board):
                    for act in pos[2]:
                        bc=deepcopy(board); self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        self._action_on_board(bc,pos,act); self._count_nodes+=1; v=self._current_eval(bc)
                        self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        if v<bv or (v==bv and random.random()<=0.5): bv,bp,ba=v,pos,act
                        if v==float('inf') and bp is None: bp,ba=(pos[0],pos[1]),(act[0],act[1])
                        beta=min(beta,bv)
                        if beta<alpha: break
                    if beta<alpha: break
                return bp,ba,bv
        else:
            if fn == 'max':
                bv,bp,ba = -float('inf'),None,None
                for pos in self._generate_move(board):
                    for act in pos[2]:
                        bc=deepcopy(board); self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        self._action_on_board(bc,pos,act); self._count_nodes+=1
                        if self._check_for_endgame(bc): v=float('inf')
                        else: _,_,v=self._alpha_beta(depth-1,bc,'min',alpha,beta)
                        self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        if v is None: continue
                        if v>bv or (v==bv and random.random()<=0.5): bv,bp,ba=v,pos,act
                        if v==-float('inf') and bp is None: bp,ba=(pos[0],pos[1]),(act[0],act[1])
                        alpha=max(alpha,bv)
                        if beta<=alpha: break
                    if beta<alpha: break
                return bp,ba,bv
            else:
                bv,bp,ba = float('inf'),None,None
                for pos in self._generate_move(board):
                    for act in pos[2]:
                        bc=deepcopy(board); self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        self._count_nodes+=1; self._action_on_board(bc,pos,act)
                        if self._check_for_endgame(bc): v=-float('inf')
                        else: _,_,v=self._alpha_beta(depth-1,bc,'max',alpha,beta)
                        self.color,self.adversary_color=self.adversary_color,self.color; self.game.turn=self.color
                        if v is None: continue
                        if v<bv or (v==bv and random.random()<=0.5): bv,bp,ba=v,(pos[0],pos[1]),(act[0],act[1])
                        if v==float('inf') and bp is None: bp,ba=(pos[0],pos[1]),(act[0],act[1])
                        beta=min(beta,bv)
                        if beta<alpha: break
                    if beta<alpha: break
                return bp,ba,bv

    def _mobility(self, board):
        my_moves = sum(len(board.legal_moves(i,j)) for i in range(8) for j in range(8)
                       if board.location(i,j).occupant is not None and board.location(i,j).occupant.color == self.eval_color)
        opp_moves= sum(len(board.legal_moves(i,j)) for i in range(8) for j in range(8)
                       if board.location(i,j).occupant is not None and board.location(i,j).occupant.color != self.eval_color)
        return my_moves - opp_moves

    def _center_bonus(self, board):
        score = 0
        for i in range(8):
            for j in range(8):
                occ = board.location(i,j).occupant
                if occ is None: continue
                mult = 1 if occ.color == self.eval_color else -1
                if (i,j) in CENTER_SQUARES:    score += 2 * mult
                elif (i,j) in NEAR_CENTER:     score += 1 * mult
        return score

    def _piece2val(self, board):
        return sum((occ.value if occ.color==self.eval_color else -occ.value)
                   for i in range(8) for j in range(8)
                   for occ in [board.location(i,j).occupant] if occ is not None)

    def _piece_and_row2val(self, board):
        score = 0
        for i in range(8):
            for j in range(8):
                occ = board.location(i,j).occupant
                if occ is None: continue
                if self.eval_color == RED:
                    score += (5+j+2*occ.king) if occ.color==self.eval_color else -(5+(8-j)+2*occ.king)
                else:
                    score += (5+(8-j)+2*occ.king) if occ.color==self.eval_color else -(5+j+2*occ.king)
        return score

    def _piece_and_board2val(self, board):
        score = 0
        for i in range(8):
            for j in range(8):
                occ = board.location(i,j).occupant
                if occ is None: continue
                mine = occ.color == self.eval_color
                if occ.king:     score += 10 if mine else -10
                elif self.eval_color == RED:
                    score += (5 if j<4 else 7) if mine else -(7 if j<4 else 5)
                else:
                    score += (7 if j<4 else 7) if mine else -(5 if j<4 else 5)
        score += self._mobility(board) * 0.5
        score += self._center_bonus(board)
        return score

    def _piece_and_board_pov2val(self, board):
        score, n = 0, 0
        for i in range(8):
            for j in range(8):
                occ = board.location(i,j).occupant
                if occ is None: continue
                n += 1
                mine = occ.color == self.eval_color
                if occ.king:     score += 10 if mine else -10
                elif self.eval_color == RED:
                    score += (5 if j<4 else 7) if mine else -(7 if j<4 else 5)
                else:
                    score += (7 if j<4 else 7) if mine else -(5 if j<4 else 5)
        score += self._center_bonus(board)
        return score / max(n,1)

    def _dist(self, x1, y1, x2, y2): return math.sqrt((x1-x2)**2+(y1-y2)**2)

    def _pieces_loc(self, board):
        pl,ad=[],[]
        for i in range(8):
            for j in range(8):
                occ=board.location(i,j).occupant
                if occ: (pl if occ.color==self.eval_color else ad).append((i,j))
        return pl,ad

    def _sum_of_dist(self, board):
        pl,ad=self._pieces_loc(board)
        d=sum(self._dist(p[0],p[1],a[0],a[1]) for p in pl for a in ad)
        return -d if len(pl)>=len(ad) else d

    def _farthest_piece(self, board):
        pl,ad=self._pieces_loc(board); d=0
        for p in pl:
            for a in ad: d=max(d,self._dist(p[0],p[1],a[0],a[1]))
        return -d if len(pl)>=len(ad) else d

    def _check_for_endgame(self, board):
        for x in range(8):
            for y in range(8):
                if (board.location(x,y).color==BLACK and board.location(x,y).occupant is not None
                        and board.location(x,y).occupant.color==self.game.turn):
                    if board.legal_moves(x,y)!=[]: return False
        return True
