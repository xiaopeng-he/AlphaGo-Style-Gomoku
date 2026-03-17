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
import collections
import pygame
import math
import json
import os
import random

MEMORY_FILE = "brain_memory.json"
memory_db = {}

def load_memory():
    global memory_db
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory_db = json.load(f)
            print(f"已加载经验记忆库，当前掌握 {len(memory_db)} 种复杂残局最优解。")
        except:
            memory_db = {}

def save_memory():
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory_db, f)

def get_board_hash(board):
    return board.tobytes().hex()

SHAPE_SCORE = collections.defaultdict(lambda: 0, {
    (1, 1, 1, 1, 1): 1000000,   
    (-1, -1, -1, -1, -1): -1000000, 
    (0, 1, 1, 1, 1, 0): 100000, 
    (0, -1, -1, -1, -1, 0): -100000,
    (0, 1, 1, 1, 1, -1): 10000,
    (-1, 1, 1, 1, 1, 0): 10000,
    (0, -1, -1, -1, -1, 1): -10000,
    (1, -1, -1, -1, -1, 0): -10000,
    (2, 1, 1, 1, 1, 0): 10000,
    (0, 1, 1, 1, 1, 2): 10000,
    (2, -1, -1, -1, -1, 0): -10000,
    (0, -1, -1, -1, -1, 2): -10000,
    (0, 1, 1, 1, 0): 8000,      
    (0, -1, -1, -1, 0): -8000,
    (0, 1, 1, 1, -1): 1000,
    (-1, 1, 1, 1, 0): 1000,
    (0, 1, 1, 1, 2): 1000,
    (2, 1, 1, 1, 0): 1000,
    (0, -1, -1, -1, 1): -1000,
    (1, -1, -1, -1, 0): -1000,
    (0, -1, -1, -1, 2): -1000,
    (2, -1, -1, -1, 0): -1000,
    (0, 1, 1, 0): 500,
    (0, -1, -1, 0): -500,
})

def evaluate_board_numpy(board, player):
    board_size = board.shape[0]
    total_score = 0
    padded_board = np.pad(board, 1, 'constant', constant_values=2)
    for row in range(1, board_size + 1):
        total_score += score_line_numpy(padded_board[row, :])
    for col in range(1, board_size + 1):
        total_score += score_line_numpy(padded_board[:, col])
    for diag_i in range(-board_size + 1, board_size):
        line = padded_board.diagonal(diag_i)
        if len(line) >= 4: total_score += score_line_numpy(line)
        line = np.fliplr(padded_board).diagonal(diag_i)
        if len(line) >= 4: total_score += score_line_numpy(line)
    return total_score * player

def score_line_numpy(line):
    line_score = 0
    for length in range(4, 7):
        if len(line) < length: continue
        windows = np.lib.stride_tricks.sliding_window_view(line, length)
        windows_tuples = map(tuple, windows)
        for w in windows_tuples:
            line_score += SHAPE_SCORE[w]
    return line_score

def evaluate_single_point_heat(board, x, y):
    board_size = board.shape[0]
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    heat = 0
    for p in [1, -1]:
        for dx, dy in directions:
            line = []
            for step in range(-4, 5):
                nx, ny = x + step*dx, y + step*dy
                if 0 <= nx < board_size and 0 <= ny < board_size:
                    if step == 0: line.append(p)
                    else: line.append(board[nx, ny])
                else:
                    line.append(2)
            heat += abs(score_line_numpy(np.array(line)))
    heat += random.uniform(0, 10)
    return heat

def get_ordered_moves_smart(board, top_k=15):
    board_size = board.shape[0]
    has_stone = (board != 0)
    if not np.any(has_stone):
        return [(board_size//2, board_size//2)]
        
    from scipy.signal import convolve2d
    kernel = np.ones((3, 3), dtype=np.int8)
    kernel[1, 1] = 0
    neighbor_counts = convolve2d(has_stone.astype(np.int8), kernel, mode='same', boundary='fill', fillvalue=0)
    
    valid_mask = (board == 0) & (neighbor_counts > 0)
    moves = np.argwhere(valid_mask).tolist()
    
    move_heats = [(evaluate_single_point_heat(board, m[0], m[1]), m) for m in moves]
    move_heats.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in move_heats][:top_k]

def minimax_alpha_beta(board, depth, alpha, beta, is_maximizing, max_player_color):
    pygame.event.pump() 
    game_result = check_game_over_engine(board)
    if depth == 0 or game_result != -2: 
        if game_result == max_player_color: return None, 10000000 + depth 
        if game_result == -max_player_color: return None, -10000000 - depth 
        if game_result == 0: return None, 0 
        return None, evaluate_board_numpy(board, max_player_color)

    top_k = 12 if depth > 4 else 8
    moves = get_ordered_moves_smart(board, top_k=top_k)
    if not moves: return None, 0 
    
    best_move = moves[0]
    if is_maximizing:
        best_val = -float('inf')
        for move in moves:
            board[move[0], move[1]] = max_player_color
            _, val = minimax_alpha_beta(board, depth - 1, alpha, beta, False, max_player_color)
            board[move[0], move[1]] = 0 
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, best_val)
            if beta <= alpha: break 
        return best_move, best_val
    else:
        best_val = float('inf')
        for move in moves:
            board[move[0], move[1]] = -max_player_color
            _, val = minimax_alpha_beta(board, depth - 1, alpha, beta, True, max_player_color)
            board[move[0], move[1]] = 0
            if val < best_val:
                best_val = val
                best_move = move
            beta = min(beta, best_val)
            if beta <= alpha: break 
        return best_move, best_val

def get_alphago_analysis_live(board, max_capacity_depth, ai_color, progress_callback=None, diversity_mode=False):
    stone_count = np.count_nonzero(board)
    if stone_count < 4:
        target_depth = 2 
    elif stone_count < 10:
        target_depth = 4 
    else:
        target_depth = max_capacity_depth 

    board_hash = get_board_hash(board)
    # 如果是在训练模式(diversity_mode)，即使命中记忆也要重新推演以探索新路线
    if not diversity_mode and board_hash in memory_db and memory_db[board_hash]['depth'] >= target_depth:
        if progress_callback: progress_callback(memory_db[board_hash]['analysis'], target_depth, target_depth, None, True)
        return memory_db[board_hash]['analysis']

    moves = get_ordered_moves_smart(board, top_k=5)
    if not moves: return []

    best_results_overall = []

    for current_depth in range(1, target_depth + 1):
        current_depth_results = []
        alpha = -float('inf')
        beta = float('inf')
        
        if best_results_overall:
            moves = [res['move'] for res in best_results_overall]

        for move in moves:
            if progress_callback:
                progress_callback(best_results_overall, current_depth, target_depth, move, False)

            board[move[0], move[1]] = ai_color
            _, score = minimax_alpha_beta(board, current_depth - 1, alpha, beta, False, ai_color)
            board[move[0], move[1]] = 0
            
            win_rate = 1.0 / (1.0 + math.exp(-max(min(score / 3000.0, 10), -10))) 
            current_depth_results.append({
                'move': move,
                'score': score,
                'win_rate': win_rate * 100 
            })
            
        current_depth_results.sort(key=lambda x: x['score'], reverse=True)
        best_results_overall = current_depth_results
        
        if progress_callback:
            progress_callback(best_results_overall, current_depth, target_depth, None, False)
            
        if best_results_overall:
            best_score = best_results_overall[0]['score']
            if best_score > 800000:
                break
            if current_depth >= 2 and len(best_results_overall) > 1:
                if best_score > -800000 and best_results_overall[1]['score'] < -800000:
                    break

    # 如果是自我对弈的前 12 步，为了增加棋谱多样性，不在一条树枝上吊死
    if diversity_mode and stone_count <= 12 and best_results_overall:
        best_score = best_results_overall[0]['score']
        # 找出所有与最优解胜率差距在 15% 以内，且没有被绝杀（分数>-800000）的候选点
        valid_candidates = [res for res in best_results_overall if best_score - res['score'] < 1500 and res['score'] > -800000]
        if len(valid_candidates) > 1:
            # 根据得分计算 softmax 概率进行轮盘赌采样
            scores = np.array([res['score'] for res in valid_candidates])
            probs = np.exp((scores - np.max(scores)) / 500.0) 
            probs /= np.sum(probs)
            chosen_idx = np.random.choice(len(valid_candidates), p=probs)
            # 把被抽中的变异基因强行提拔到第 0 位
            chosen_res = valid_candidates[chosen_idx]
            best_results_overall.remove(chosen_res)
            best_results_overall.insert(0, chosen_res)

    memory_db[board_hash] = {'depth': target_depth, 'analysis': best_results_overall}
    save_memory()
    
    if progress_callback: progress_callback(best_results_overall, current_depth, target_depth, None, True)
    return best_results_overall

def check_game_over_engine(board):
    if not np.any(board == 0): return 0
    def check_five_numpy(b, player):
        h = np.array([[1, 1, 1, 1, 1]], dtype=np.int8)
        v = h.T                                                       
        d1 = np.eye(5, dtype=np.int8)
        d2 = np.fliplr(np.eye(5, dtype=np.int8))
        from scipy.signal import convolve2d
        if np.any(convolve2d(b, h, mode='valid') == 5 * player): return True
        if np.any(convolve2d(b, v, mode='valid') == 5 * player): return True
        if np.any(convolve2d(b, d1, mode='valid') == 5 * player): return True
        if np.any(convolve2d(b, d2, mode='valid') == 5 * player): return True
        return False
    if check_five_numpy(board, 1): return 1
    if check_five_numpy(board, -1): return -1
    return -2 

load_memory()