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
import pygame
import sys
import threading
import datetime
import math  
import os
import json
from env import GomokuEnv
from engine import get_alphago_analysis_live, MEMORY_FILE

X_AXIS_CHARS = "ABCDEFGHIJKLMNO"
Y_AXIS_CHARS = [str(i) for i in range(1, 16)]

def get_coord_str(x, y):
    return f"{X_AXIS_CHARS[x]}{Y_AXIS_CHARS[y]}"

def generate_report(history_log, winner, human_color):
    filename = f"match_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# 确定性验证局 - 赛后质量审查报告\n\n")
        f.write(f"- **对局时间：** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if winner == human_color: result = "人类玩家胜"
        elif winner == -human_color: result = "AI 胜"
        else: result = "平局"
        f.write(f"- **对局结果：** {result}\n\n")
        f.write("### 关键胜率波动（恶手与妙手监测）\n")
        f.write("| 手数 | 执子 | 战术坐标 | 落子前 AI 胜率评估 | 评级 |\n")
        f.write("|---|---|---|---|---|\n")
        for i in range(1, len(history_log)):
            prev = history_log[i-1]
            curr = history_log[i]
            if prev['win_rate_before_move'] is None or curr['win_rate_before_move'] is None: continue
            win_rate_diff = curr['win_rate_before_move'] - prev['win_rate_before_move']
            player_str = "人类" if prev['player'] == human_color else "AI"
            eval_str = "-"
            if prev['player'] == human_color and win_rate_diff > 15.0: eval_str = "🚨 严重失误 (恶手)"
            elif prev['player'] == human_color and win_rate_diff < -5.0: eval_str = "🌟 绝妙一击 (妙手)"
            coord = get_coord_str(prev['move'][0], prev['move'][1])
            f.write(f"| {i} | {player_str} | {coord} | {prev['win_rate_before_move']:.1f}% | {eval_str} |\n")
    print(f"\n[系统通知] 赛后复盘分析已生成：{filename}")

# ==================== 模式一：人机双轨实战台 ====================
def play_vs_ai_dual_board():
    board_size = 15
    env = GomokuEnv(board_size)
    MAX_CAPACITY_DEPTH = 6 
    
    pygame.init()
    grid_size = 30 
    margin = 35
    board_px = grid_size * (board_size - 1) + 2 * margin 
    
    analysis_panel_width = 320
    window_width = board_px * 2 + analysis_panel_width
    window_height = board_px
    
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("AlphaGo-Style 五子棋对弈平台【he_xp815@hotmail.com】")
    font = pygame.font.SysFont("simhei", 14)
    axis_font = pygame.font.SysFont("arial", 12, bold=True)
    large_font = pygame.font.SysFont("simhei", 18, bold=True)
    
    human_color = 1  
    ai_color = -1    
    hover_pos = None 
    
    analysis_data = {
        'is_computing': False,
        'results': [],
        'win_rate_history': [50.0],
        'board_version': 0,
        'live_depth': 0,        
        'target_depth': 0,     
        'live_focus_move': None 
    }

    def ui_progress_callback(intermediate_results, depth, target_depth, focus_move, is_done, version, player_color):
        if analysis_data['board_version'] != version: return 
        analysis_data['results'] = list(intermediate_results)
        analysis_data['live_depth'] = depth
        analysis_data['target_depth'] = target_depth
        analysis_data['live_focus_move'] = focus_move
        if is_done:
            if intermediate_results and player_color == ai_color:
                analysis_data['win_rate_history'].append(intermediate_results[0]['win_rate'])
            analysis_data['is_computing'] = False

    def async_compute_analysis(board_copy, player_color, version):
        def callback_wrapper(res, current_d, target_d, fm, done):
            ui_progress_callback(res, current_d, target_d, fm, done, version, player_color)
        get_alphago_analysis_live(board_copy, MAX_CAPACITY_DEPTH, player_color, progress_callback=callback_wrapper, diversity_mode=False)

    def draw_graph(rect_x, rect_y, rect_w, rect_h):
        pygame.draw.rect(screen, (30, 33, 39), (rect_x, rect_y, rect_w, rect_h))
        pygame.draw.line(screen, (100, 100, 100), (rect_x, rect_y + rect_h//2), (rect_x + rect_w, rect_y + rect_h//2), 1)
        history = analysis_data['win_rate_history']
        if len(history) < 2: return
        point_spacing = rect_w / max(10, len(history) - 1)
        points = []
        for i, rate in enumerate(history):
            px = rect_x + i * point_spacing
            py = rect_y + rect_h - (rate / 100.0 * rect_h)
            points.append((px, py))
        pygame.draw.lines(screen, (97, 175, 239), False, points, 2)
        pygame.draw.circle(screen, (224, 108, 117), (int(points[-1][0]), int(points[-1][1])), 4)

    def draw_board():
        screen.fill((25, 28, 33)) 
        
        def render_single_board(offset_x, title_text, bg_color):
            pygame.draw.rect(screen, bg_color, (offset_x, 0, board_px, window_height))
            for i in range(board_size):
                line_pos = margin + i * grid_size
                pygame.draw.line(screen, (0,0,0), (offset_x + margin, line_pos), (offset_x + board_px-margin, line_pos))
                pygame.draw.line(screen, (0,0,0), (offset_x + line_pos, margin), (offset_x + line_pos, window_height-margin))
                
                char_render = axis_font.render(X_AXIS_CHARS[i], True, (80, 80, 80))
                screen.blit(char_render, (offset_x + line_pos - 5, margin - 22))
                screen.blit(char_render, (offset_x + line_pos - 5, window_height - margin + 8))
                
                num_render = axis_font.render(Y_AXIS_CHARS[i], True, (80, 80, 80))
                screen.blit(num_render, (offset_x + margin - 25, line_pos - 7))
                screen.blit(num_render, (offset_x + board_px - margin + 8, line_pos - 7))

            for x in range(board_size):
                for y in range(board_size):
                    center = (offset_x + margin + x*grid_size, margin + y*grid_size)
                    if env.board[x, y] == 1:
                        pygame.draw.circle(screen, (0,0,0), center, grid_size//2 - 2)
                        if env.last_move == (x, y): pygame.draw.circle(screen, (255,0,0), center, grid_size//4, 2)
                    elif env.board[x, y] == -1:
                        pygame.draw.circle(screen, (255,255,255), center, grid_size//2 - 2)
                        if env.last_move == (x, y): pygame.draw.circle(screen, (255,0,0), center, grid_size//4, 2)
            title_render = large_font.render(title_text, True, (0, 0, 0))
            screen.blit(title_render, (offset_x + 10, 10))

        render_single_board(0, "主战场 (人类操作区)", (222, 184, 135))
        if hover_pos and env.current_player == human_color and not env.game_over:
            hx, hy = hover_pos
            if 0 <= hx < board_size and 0 <= hy < board_size and env.board[hx, hy] == 0:
                ghost_surface = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
                pygame.draw.circle(ghost_surface, (0, 0, 0, 100), (grid_size//2, grid_size//2), grid_size//2 - 2)
                screen.blit(ghost_surface, (margin + hx*grid_size - grid_size//2, margin + hy*grid_size - grid_size//2))

        render_single_board(board_px, "上帝沙盘 (全息透视层)", (200, 205, 215))
        
        if analysis_data['results'] and not env.game_over:
            for idx, data in enumerate(analysis_data['results']):
                mx, my = data['move']
                center = (board_px + margin + mx*grid_size, margin + my*grid_size)
                color = (0, 180, 0) if idx == 0 else (0, 100, 255)
                pygame.draw.rect(screen, color, (center[0]-grid_size//2+2, center[1]-grid_size//2+2, grid_size-4, grid_size-4), 2)
                num_text = font.render(str(idx+1), True, color)
                screen.blit(num_text, (center[0] - 4, center[1] - 8))
                
        if analysis_data['is_computing'] and analysis_data['live_focus_move']:
            fx, fy = analysis_data['live_focus_move']
            center = (board_px + margin + fx*grid_size, margin + fy*grid_size)
            pulse = abs(math.sin(pygame.time.get_ticks() / 150.0)) * 255
            pygame.draw.circle(screen, (int(pulse), 0, 0), center, grid_size//2 + 2, 2)

        panel_x = board_px * 2
        pygame.draw.rect(screen, (40, 44, 52), (panel_x, 0, analysis_panel_width, window_height))
        title = large_font.render("对局状态监测系统", True, (255, 255, 255))
        screen.blit(title, (panel_x + 20, 20))
        
        target_player = "人类" if env.current_player == human_color else "AI"
        if analysis_data['is_computing']:
            status_text = font.render(f"正在演算 [{target_player}] | 深度: {analysis_data['live_depth']} (目标: {analysis_data['target_depth']})", True, (229, 192, 123))
        else:
            status_text = font.render(f"演算完成 | [{target_player}] 选点如沙盘所示", True, (152, 195, 121))
        screen.blit(status_text, (panel_x + 20, 50))
        
        undo_prompt = font.render("按 [Backspace] 退格键进行悔棋回溯", True, (171, 178, 191))
        screen.blit(undo_prompt, (panel_x + 20, 75))
        
        y_offset = 110
        for idx, data in enumerate(analysis_data['results']):
            mx, my = data['move']
            marker = "最优 ►" if idx == 0 else "候选  "
            color = (152, 195, 121) if idx == 0 else (171, 178, 191)
            if analysis_data['is_computing'] and analysis_data['live_focus_move'] == (mx, my):
                color = (229, 192, 123)
                marker = "探测 ↻"
            
            coord_str = get_coord_str(mx, my)
            row_text = font.render(f"{marker} {coord_str} | 胜率: {data['win_rate']:.1f}%", True, color)
            screen.blit(row_text, (panel_x + 20, y_offset))
            y_offset += 25
            
        graph_h = 130
        graph_w = analysis_panel_width - 40
        draw_graph(panel_x + 20, window_height - graph_h - 20, graph_w, graph_h)
        graph_title = font.render("全局胜率波动图 (Y轴:胜率 X轴:手数)", True, (171, 178, 191))
        screen.blit(graph_title, (panel_x + 20, window_height - graph_h - 45))


        brand_text = font.render("AlphaGo-Style 五子棋对弈平台", True, (90, 95, 105))
        author_text = font.render("Engineered by: xiaopeng_he", True, (90, 95, 105))
        email_text = font.render("Contact:: he_xp815@hotmail.com", True, (90, 95, 105))
        screen.blit(brand_text, (panel_x + 20, window_height - 65))
        screen.blit(author_text, (panel_x + 20, window_height - 40))
        screen.blit(email_text, (panel_x + 20, window_height - 20))

        pygame.display.flip()


    draw_board()
    analysis_data['is_computing'] = True
    threading.Thread(target=async_compute_analysis, args=(env.board.copy(), human_color, analysis_data['board_version']), daemon=True).start()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if env.undo():
                        analysis_data['board_version'] += 1
                        analysis_data['results'] = []
                        if len(analysis_data['win_rate_history']) > 2:
                            analysis_data['win_rate_history'] = analysis_data['win_rate_history'][:-2]
                        analysis_data['is_computing'] = True
                        draw_board()
                        threading.Thread(target=async_compute_analysis, args=(env.board.copy(), env.current_player, analysis_data['board_version']), daemon=True).start()

            elif event.type == pygame.MOUSEMOTION:
                pos = event.pos
                if pos[0] < board_px: 
                    hx = round((pos[0] - margin) / grid_size)
                    hy = round((pos[1] - margin) / grid_size)
                    hover_pos = (hx, hy)
                else:
                    hover_pos = None
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if env.current_player == human_color and not env.game_over:
                    pos = event.pos
                    if pos[0] < board_px: 
                        x = round((pos[0] - margin) / grid_size)
                        y = round((pos[1] - margin) / grid_size)
                        current_win_rate = analysis_data['win_rate_history'][-1] if analysis_data['win_rate_history'] else 50.0
                        if 0 <= x < board_size and 0 <= y < board_size and env.board[x, y] == 0:
                            if env.step(x, y, current_win_rate):
                                analysis_data['board_version'] += 1
                                analysis_data['results'] = [] 
                                if env.game_over:
                                    print("人类获得了胜利！")
                                    generate_report(env.history_log, env.winner, human_color)
                                else:
                                    analysis_data['is_computing'] = True
                                    threading.Thread(target=async_compute_analysis, args=(env.board.copy(), ai_color, analysis_data['board_version']), daemon=True).start()

        if env.current_player == ai_color and not env.game_over:
            if not analysis_data['is_computing'] and analysis_data['results']:
                best_move = analysis_data['results'][0]['move']
                current_win_rate = analysis_data['win_rate_history'][-1] if analysis_data['win_rate_history'] else 50.0
                env.step(best_move[0], best_move[1], current_win_rate)
                analysis_data['board_version'] += 1
                analysis_data['results'] = []
                if env.game_over:
                    print("AI获得了胜利！")
                    generate_report(env.history_log, env.winner, human_color)
                else:
                    analysis_data['is_computing'] = True
                    threading.Thread(target=async_compute_analysis, args=(env.board.copy(), human_color, analysis_data['board_version']), daemon=True).start()

        draw_board() 

# ==================== 模式二：AI 精神时光屋 (自我演化管道) ====================
def run_hyperbolic_time_chamber():
    board_size = 15
    MAX_CAPACITY_DEPTH = 4 # 时光屋为了走量，深度挂4档即可，重点在于填充哈希记忆表
    
    pygame.init()
    grid_size = 30
    margin = 35
    board_px = grid_size * (board_size - 1) + 2 * margin
    
    # 只有一个棋盘和一个极其简洁的数据监控屏
    panel_width = 300
    screen = pygame.display.set_mode((board_px + panel_width, board_px))
    pygame.display.set_caption("AI 自训练小黑屋 (自我对弈训练矩阵)")
    font = pygame.font.SysFont("simhei", 16)
    large_font = pygame.font.SysFont("simhei", 24, bold=True)
    
    games_played = 0
    black_wins = 0
    white_wins = 0
    draws = 0
    
    while True:
        env = GomokuEnv(board_size)
        games_played += 1
        print(f"\n🚀 正在启动第 {games_played} 个平行宇宙进行演化...")
        
        while not env.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
            # 调用带量子扰动的搜索，保证棋局的多样性
            results = get_alphago_analysis_live(env.board.copy(), MAX_CAPACITY_DEPTH, env.current_player, diversity_mode=True)
            if results:
                best_move = results[0]['move']
                env.step(best_move[0], best_move[1], results[0]['win_rate'])
            else:
                env.game_over = True
                
            # --- 极速渲染 ---
            screen.fill((25, 28, 33))
            pygame.draw.rect(screen, (200, 205, 215), (0, 0, board_px, board_px))
            for i in range(board_size):
                line_pos = margin + i * grid_size
                pygame.draw.line(screen, (0,0,0), (margin, line_pos), (board_px-margin, line_pos))
                pygame.draw.line(screen, (0,0,0), (line_pos, margin), (line_pos, board_px-margin))
            
            for x in range(board_size):
                for y in range(board_size):
                    center = (margin + x*grid_size, margin + y*grid_size)
                    if env.board[x, y] == 1: pygame.draw.circle(screen, (0,0,0), center, grid_size//2 - 2)
                    elif env.board[x, y] == -1: pygame.draw.circle(screen, (255,255,255), center, grid_size//2 - 2)
            
            # 右侧状态栏
            pygame.draw.rect(screen, (40, 44, 52), (board_px, 0, panel_width, board_px))
            screen.blit(large_font.render("自训练屋演化监控屏", True, (255, 255, 255)), (board_px + 20, 20))
            screen.blit(font.render(f"当前对局：第 {games_played} 局", True, (97, 175, 239)), (board_px + 20, 80))
            screen.blit(font.render(f"黑方胜场：{black_wins}", True, (152, 195, 121)), (board_px + 20, 120))
            screen.blit(font.render(f"白方胜场：{white_wins}", True, (229, 192, 123)), (board_px + 20, 150))
            screen.blit(font.render(f"平局数量：{draws}", True, (171, 178, 191)), (board_px + 20, 180))
            
            try:
                mem_size = os.path.getsize(MEMORY_FILE) / 1024
            except:
                mem_size = 0
            screen.blit(font.render(f"记忆库(错题本)大小: {mem_size:.1f} KB", True, (224, 108, 117)), (board_px + 20, 240))
            
            pygame.display.flip()
            
        if env.winner == 1: black_wins += 1
        elif env.winner == -1: white_wins += 1
        else: draws += 1

if __name__ == "__main__":
    print("=================================================")
    print("      AlphaGO-Style 五子棋 AI 架构测试终端")
    print("=================================================")
    print("1. 启动 [人机双轨实战台] (支持悔棋/坐标/分析)")
    print("2. 启动 [AI 自训练小黑屋] (自动对弈丰富错题本)")
    choice = input("请输入启动指令 (1 或 2): ")
    
    if choice == '1':
        play_vs_ai_dual_board()
    elif choice == '2':
        run_hyperbolic_time_chamber()
    else:
        print("无效指令，终端关闭。")