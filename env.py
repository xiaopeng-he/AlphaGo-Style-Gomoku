# ==============================================================================
#    ___   __      __       __             _____     ____        __         
#   / _ | / /___  / /  ___ / /  ___  ___  / __/ /_  __\ \  __ __/ /__       
#  / __ |/ / / / / _ \/ _ `/ _ \/ _ \/___/\ \/ __/ / -_)_\ \/ // / / -_)      
# /_/ |_/_/_/ /_/_//_/\_,_/_//_/\___/   /___/\__/  \__//_/\_, /_/\__/       
#                                                        /___/              
# ==============================================================================
# Project: AlphaGo-Style 五子棋对弈平台 (AlphaGo-Style Gomoku Platform)
# Author:  xiaopeng_he
# Contact: he_xp815@hotmail.com
# 
# Copyright (c) 2026 he_xp815. All rights reserved.
# 本系统架构受版权保护。保留原作者署名权，禁止恶意抹除或篡改核心版权信息。
# ==============================================================================
import numpy as np

class GomokuEnv:
    def __init__(self, board_size=15):
        self.board_size = board_size
        self.board = np.zeros((board_size, board_size), dtype=np.int8)
        self.current_player = 1 
        self.game_over = False
        self.winner = 0
        self.last_move = None
        self.history_log = [] 

    def step(self, x, y, win_rate_estimation=None):
        if self.game_over or x < 0 or x >= self.board_size or y < 0 or y >= self.board_size or self.board[x, y] != 0:
            return False
            
        self.board[x, y] = self.current_player
        self.last_move = (x, y)
        
        self.history_log.append({
            'player': self.current_player,
            'move': (x, y),
            'win_rate_before_move': win_rate_estimation
        })
        
        if not np.any(self.board == 0):
            self.game_over = True
            self.winner = 0
            return True

        if self._check_win_numpy(x, y, self.current_player):
            self.game_over = True
            self.winner = self.current_player
        else:
            self.current_player *= -1
                
        return True

    def _check_win_numpy(self, x, y, player):
        def count_in_dir(dx, dy):
            count = 0
            nx, ny = x + dx, y + dy
            while 0 <= nx < self.board_size and 0 <= ny < self.board_size and self.board[nx, ny] == player:
                count += 1
                nx += dx; ny += dy
            return count
            
        directions = [(1,0), (0,1), (1,1), (1,-1)]
        for dx, dy in directions:
            if count_in_dir(dx, dy) + count_in_dir(-dx, -dy) + 1 >= 5:
                return True
        return False

    def undo(self):
        """
        【时间回溯引擎】回滚一整个回合（剥离人类的恶手和 AI 的回应）
        """
        if len(self.history_log) >= 2:
            self.history_log = self.history_log[:-2]
            
            self.board = np.zeros((self.board_size, self.board_size), dtype=np.int8)
            self.current_player = 1
            self.game_over = False
            self.winner = 0
            self.last_move = None
            
            for action in self.history_log:
                x, y = action['move']
                self.board[x, y] = self.current_player
                self.last_move = (x, y)
                self.current_player *= -1
            return True
        return False