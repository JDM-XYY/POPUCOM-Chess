import pygame
import sys
import numpy as np
import os
from pygame.locals import *

# 初始化pygame
pygame.init()

# 游戏常量
BOARD_SIZE = 9
CELL_SIZE = 60
MARGIN = 50
WINDOW_SIZE = 2 * MARGIN + BOARD_SIZE * CELL_SIZE
FPS = 60

# 颜色定义
BACKGROUND = (28, 35, 43)
GRID_COLOR = (60, 70, 90)
PLAYER1_COLOR = (255, 107, 107)  # 红色
PLAYER1_TERRITORY = (100, 30, 30, 150)  # 玩家1占领区域 (半透明)
PLAYER2_COLOR = (107, 178, 255)  # 蓝色
PLAYER2_TERRITORY = (30, 60, 100, 150)  # 玩家2占领区域 (半透明)
HIGHLIGHT_COLOR = (255, 215, 0)  # 金色
TEXT_COLOR = (240, 240, 240)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 160, 210)

# 创建游戏窗口
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 100))
pygame.display.set_caption("泡姆三消棋")
clock = pygame.time.Clock()


# 解决中文显示问题
def load_font(size):
    """尝试加载多个字体以解决中文显示问题"""
    # 尝试常见的中文字体
    font_names = [
        'SimHei', 'Microsoft YaHei', 'KaiTi', 'SimSun',
        'FangSong', 'STHeiti', 'STKaiti', 'STSong',
        'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei'
    ]

    # 尝试加载系统字体
    for name in font_names:
        try:
            font = pygame.font.SysFont(name, size)
            # 测试字体是否能显示中文
            test_surface = font.render("测试", True, (255, 255, 255))
            if test_surface.get_width() > 0:
                return font
        except:
            continue

    # 如果都失败，使用默认字体（可能无法显示中文）
    return pygame.font.SysFont(None, size)


# 字体
font = load_font(25)
small_font = load_font(20)


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        # 初始化棋盘 (0=空, 1=玩家1, 2=玩家2)
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        # 领地状态 (0=无主, 1=玩家1领地, 2=玩家2领地)
        self.territory = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        self.current_player = 1  # 玩家1先手
        self.total_moves = 0
        self.max_moves = 50
        self.game_over = False
        self.winner = None
        self.last_move_pos = None

    def make_move(self, row, col):
        # 如果游戏结束，则不能落子
        if self.game_over:
            return False

        # 检查位置是否已被占用
        if self.board[row][col] != 0:  # 位置已有棋子
            return False

        # 检查位置是否已被对方占领
        if self.territory[row][col] == 3 - self.current_player:
            return False

        # 落子
        self.board[row][col] = self.current_player
        self.last_move_pos = (row, col)
        self.total_moves += 1

        # 检查是否形成三消并自动处理所有三消
        self.process_eliminations()

        # 切换到下一位玩家
        self.current_player = 3 - self.current_player  # 切换玩家 (1->2, 2->1)

        # 检查游戏是否结束
        if self.total_moves >= self.max_moves:
            self.end_game()

        return True

    def process_eliminations(self):
        """检查并处理所有三消（删除棋子并占领领地）"""
        player = self.current_player
        eliminations = []  # 存储所有三消事件

        # 检查整个棋盘上的所有三消可能性
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # 检查水平方向
                if col <= BOARD_SIZE - 3:
                    if self.board[row][col] == player and \
                            self.board[row][col + 1] == player and \
                            self.board[row][col + 2] == player:
                        eliminations.append(('horizontal', (row, col), (row, col + 2)))

                # 检查垂直方向
                if row <= BOARD_SIZE - 3:
                    if self.board[row][col] == player and \
                            self.board[row + 1][col] == player and \
                            self.board[row + 2][col] == player:
                        eliminations.append(('vertical', (row, col), (row + 2, col)))

                # 检查主对角线 (左上到右下)
                if row <= BOARD_SIZE - 3 and col <= BOARD_SIZE - 3:
                    if self.board[row][col] == player and \
                            self.board[row + 1][col + 1] == player and \
                            self.board[row + 2][col + 2] == player:
                        eliminations.append(('diagonal1', (row, col), (row + 2, col + 2)))

                # 检查副对角线 (右上到左下)
                if row <= BOARD_SIZE - 3 and col >= 2:
                    if self.board[row][col] == player and \
                            self.board[row + 1][col - 1] == player and \
                            self.board[row + 2][col - 2] == player:
                        eliminations.append(('diagonal2', (row, col), (row + 2, col - 2)))

        # 处理所有三消
        for elimination in eliminations:
            direction, start, end = elimination
            self.remove_elimination_tiles(direction, start, end)
            self.claim_line(direction, start, end)

    def remove_elimination_tiles(self, direction, start, end):
        """删除形成三消的三个棋子"""
        if direction == 'horizontal':
            row, start_col = start
            _, end_col = end
            for col in range(start_col, end_col + 1):
                self.board[row][col] = 0

        elif direction == 'vertical':
            start_row, col = start
            end_row, _ = end
            for row in range(start_row, end_row + 1):
                self.board[row][col] = 0

        elif direction == 'diagonal1':  # 主对角线 (左上到右下)
            start_row, start_col = start
            end_row, end_col = end
            r, c = start_row, start_col
            while r <= end_row and c <= end_col:
                self.board[r][c] = 0
                r += 1
                c += 1

        elif direction == 'diagonal2':  # 副对角线 (右上到左下)
            start_row, start_col = start
            end_row, end_col = end
            r, c = start_row, start_col
            while r <= end_row and c >= end_col:
                self.board[r][c] = 0
                r += 1
                c -= 1

    def claim_line(self, direction, start, end):
        """从三消点向两边发散占领线（遇到对方棋子会中断），包含三消棋子所在的格子"""
        opponent = 3 - self.current_player

        if direction == 'horizontal':
            # 从三消点向两边发散
            row = start[0]
            start_col = min(start[1], end[1])
            end_col = max(start[1], end[1])

            # 首先占领三消的三个格子
            for c in range(start_col, end_col + 1):
                self.territory[row][c] = self.current_player

            # 向左占领（包含三消点）
            for c in range(start_col, -1, -1):
                if self.board[row][c] == opponent:
                    break
                self.territory[row][c] = self.current_player
                # 如果遇到边界或对方棋子，停止向左扩展
                if c > 0 and self.board[row][c - 1] == opponent:
                    break

            # 向右占领（包含三消点）
            for c in range(end_col, BOARD_SIZE):
                if self.board[row][c] == opponent:
                    break
                self.territory[row][c] = self.current_player
                # 如果遇到边界或对方棋子，停止向右扩展
                if c < BOARD_SIZE - 1 and self.board[row][c + 1] == opponent:
                    break

        elif direction == 'vertical':
            # 从三消点向两边发散
            col = start[1]
            start_row = min(start[0], end[0])
            end_row = max(start[0], end[0])

            # 首先占领三消的三个格子
            for r in range(start_row, end_row + 1):
                self.territory[r][col] = self.current_player

            # 向上占领（包含三消点）
            for r in range(start_row, -1, -1):
                if self.board[r][col] == opponent:
                    break
                self.territory[r][col] = self.current_player
                # 如果遇到边界或对方棋子，停止向上扩展
                if r > 0 and self.board[r - 1][col] == opponent:
                    break

            # 向下占领（包含三消点）
            for r in range(end_row, BOARD_SIZE):
                if self.board[r][col] == opponent:
                    break
                self.territory[r][col] = self.current_player
                # 如果遇到边界或对方棋子，停止向下扩展
                if r < BOARD_SIZE - 1 and self.board[r + 1][col] == opponent:
                    break

        elif direction == 'diagonal1':  # 主对角线 (左上到右下)
            # 从三消点向两边发散
            # 计算三消点
            r1, c1 = start
            r2, c2 = end
            start_r = min(r1, r2)
            start_c = min(c1, c2)
            end_r = max(r1, r2)
            end_c = max(c1, c2)

            # 首先占领三消的三个格子
            r, c = start_r, start_c
            while r <= end_r and c <= end_c:
                self.territory[r][c] = self.current_player
                r += 1
                c += 1

            # 左上方向（包含三消点）
            r, c = start_r, start_c
            while r >= 0 and c >= 0:
                if self.board[r][c] == opponent:
                    break
                self.territory[r][c] = self.current_player
                # 如果遇到边界或对方棋子，停止扩展
                if r > 0 and c > 0 and self.board[r - 1][c - 1] == opponent:
                    break
                r -= 1
                c -= 1

            # 右下方向（包含三消点）
            r, c = end_r, end_c
            while r < BOARD_SIZE and c < BOARD_SIZE:
                if self.board[r][c] == opponent:
                    break
                self.territory[r][c] = self.current_player
                # 如果遇到边界或对方棋子，停止扩展
                if r < BOARD_SIZE - 1 and c < BOARD_SIZE - 1 and self.board[r + 1][c + 1] == opponent:
                    break
                r += 1
                c += 1

        elif direction == 'diagonal2':  # 副对角线 (右上到左下)
            # 从三消点向两边发散
            # 计算三消点
            r1, c1 = start
            r2, c2 = end
            start_r = min(r1, r2)
            start_c = max(c1, c2)  # 注意：副对角线列是递减的
            end_r = max(r1, r2)
            end_c = min(c1, c2)

            # 首先占领三消的三个格子
            r, c = start_r, start_c
            while r <= end_r and c >= end_c:
                self.territory[r][c] = self.current_player
                r += 1
                c -= 1

            # 右上方向（包含三消点）
            r, c = start_r, start_c
            while r >= 0 and c < BOARD_SIZE:
                if self.board[r][c] == opponent:
                    break
                self.territory[r][c] = self.current_player
                # 如果遇到边界或对方棋子，停止扩展
                if r > 0 and c < BOARD_SIZE - 1 and self.board[r - 1][c + 1] == opponent:
                    break
                r -= 1
                c += 1

            # 左下方向（包含三消点）
            r, c = end_r, end_c
            while r < BOARD_SIZE and c >= 0:
                if self.board[r][c] == opponent:
                    break
                self.territory[r][c] = self.current_player
                # 如果遇到边界或对方棋子，停止扩展
                if r < BOARD_SIZE - 1 and c > 0 and self.board[r + 1][c - 1] == opponent:
                    break
                r += 1
                c -= 1

    def end_game(self):
        """结束游戏并确定获胜者"""
        self.game_over = True
        # 计算双方领地数
        player1_count = np.sum(self.territory == 1)
        player2_count = np.sum(self.territory == 2)

        if player1_count > player2_count:
            self.winner = 1
        elif player2_count > player1_count:
            self.winner = 2
        else:
            self.winner = 0  # 平局

    def get_score(self):
        """返回双方领地分数"""
        return np.sum(self.territory == 1), np.sum(self.territory == 2)


def draw_board(game):
    """绘制棋盘、领地和棋子"""
    screen.fill(BACKGROUND)

    # 绘制领地背景
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            rect = pygame.Rect(MARGIN + c * CELL_SIZE, MARGIN + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if game.territory[r][c] == 1:
                pygame.draw.rect(screen, PLAYER1_TERRITORY, rect)
            elif game.territory[r][c] == 2:
                pygame.draw.rect(screen, PLAYER2_TERRITORY, rect)

    # 绘制网格
    for i in range(BOARD_SIZE + 1):
        # 水平线
        pygame.draw.line(screen, GRID_COLOR,
                         (MARGIN, MARGIN + i * CELL_SIZE),
                         (MARGIN + BOARD_SIZE * CELL_SIZE, MARGIN + i * CELL_SIZE), 2)
        # 垂直线
        pygame.draw.line(screen, GRID_COLOR,
                         (MARGIN + i * CELL_SIZE, MARGIN),
                         (MARGIN + i * CELL_SIZE, MARGIN + BOARD_SIZE * CELL_SIZE), 2)

    # 绘制棋子
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            center_x = MARGIN + col * CELL_SIZE + CELL_SIZE // 2
            center_y = MARGIN + row * CELL_SIZE + CELL_SIZE // 2

            if game.board[row][col] == 1:  # 玩家1
                pygame.draw.circle(screen, PLAYER1_COLOR, (center_x, center_y), CELL_SIZE // 2 - 5)
            elif game.board[row][col] == 2:  # 玩家2
                pygame.draw.circle(screen, PLAYER2_COLOR, (center_x, center_y), CELL_SIZE // 2 - 5)

    # 高亮显示最后一步
    if game.last_move_pos:
        row, col = game.last_move_pos
        center_x = MARGIN + col * CELL_SIZE + CELL_SIZE // 2
        center_y = MARGIN + row * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, HIGHLIGHT_COLOR, (center_x, center_y), CELL_SIZE // 2 - 2, 2)

    # 绘制状态信息
    return draw_status(game)


def draw_status(game):
    """绘制游戏状态信息"""
    # 绘制玩家信息
    player1_score, player2_score = game.get_score()
    player1_text = f"玩家1领地: {player1_score}"
    player2_text = f"玩家2领地: {player2_score}"

    player1_surface = font.render(player1_text, True, PLAYER1_COLOR)
    player2_surface = font.render(player2_text, True, PLAYER2_COLOR)

    screen.blit(player1_surface, (MARGIN, WINDOW_SIZE - 30))
    screen.blit(player2_surface, (WINDOW_SIZE - MARGIN - player2_surface.get_width(), WINDOW_SIZE - 30))

    # 绘制剩余步数
    moves_text = f"剩余步数: {game.max_moves - game.total_moves}"
    moves_surface = font.render(moves_text, True, TEXT_COLOR)
    screen.blit(moves_surface, (WINDOW_SIZE // 2 - moves_surface.get_width() // 2, WINDOW_SIZE - 30))

    # 绘制当前玩家
    if not game.game_over:
        current_player = "玩家1" if game.current_player == 1 else "玩家2"
        player_color = PLAYER1_COLOR if game.current_player == 1 else PLAYER2_COLOR
        turn_text = f"当前回合: {current_player}"
        turn_surface = font.render(turn_text, True, player_color)
        screen.blit(turn_surface, (WINDOW_SIZE // 2 - turn_surface.get_width() // 2, 15))

    # 绘制游戏结束信息
    if game.game_over:
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        if game.winner == 0:
            result_text = "游戏结束: 平局!"
            color = TEXT_COLOR
        else:
            result_text = f"游戏结束: 玩家{game.winner}获胜!"
            color = PLAYER1_COLOR if game.winner == 1 else PLAYER2_COLOR

        result_surface = font.render(result_text, True, color)
        screen.blit(result_surface, (WINDOW_SIZE // 2 - result_surface.get_width() // 2, WINDOW_SIZE // 2 - 30))

        # 显示领地数
        score_text = f"玩家1: {player1_score} 领地 | 玩家2: {player2_score} 领地"
        score_surface = small_font.render(score_text, True, TEXT_COLOR)
        screen.blit(score_surface, (WINDOW_SIZE // 2 - score_surface.get_width() // 2, WINDOW_SIZE // 2 + 10))

        # 绘制重新开始按钮
        button_rect = pygame.Rect(WINDOW_SIZE // 2 - 80, WINDOW_SIZE // 2 + 50, 160, 40)
        pygame.draw.rect(screen, BUTTON_COLOR, button_rect, border_radius=10)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, button_rect, 2, border_radius=10)

        restart_text = small_font.render("重新开始", True, TEXT_COLOR)
        screen.blit(restart_text, (button_rect.centerx - restart_text.get_width() // 2,
                                   button_rect.centery - restart_text.get_height() // 2))

        return button_rect

    return None


def main():
    game = Game()
    restart_button = None

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == MOUSEBUTTONDOWN:
                if game.game_over and restart_button and restart_button.collidepoint(mouse_pos):
                    game.reset()
                    continue

                if not game.game_over:
                    # 计算点击的棋盘位置
                    if MARGIN <= mouse_pos[0] < MARGIN + BOARD_SIZE * CELL_SIZE and \
                            MARGIN <= mouse_pos[1] < MARGIN + BOARD_SIZE * CELL_SIZE:
                        col = (mouse_pos[0] - MARGIN) // CELL_SIZE
                        row = (mouse_pos[1] - MARGIN) // CELL_SIZE
                        game.make_move(row, col)

        # 绘制游戏
        restart_button = draw_board(game)

        # 如果游戏结束，检查重新开始按钮的悬停效果
        if game.game_over and restart_button:
            if restart_button.collidepoint(mouse_pos):
                pygame.draw.rect(screen, BUTTON_HOVER_COLOR, restart_button, border_radius=10)
                pygame.draw.rect(screen, HIGHLIGHT_COLOR, restart_button, 2, border_radius=10)

                restart_text = small_font.render("重新开始", True, TEXT_COLOR)
                screen.blit(restart_text, (restart_button.centerx - restart_text.get_width() // 2,
                                           restart_button.centery - restart_text.get_height() // 2))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()