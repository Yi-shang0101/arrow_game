"""一箭又一箭：Pygame 界面。运行 python main.py。"""
import math
import os
from pathlib import Path

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame
from levels import LEVELS
from logic import DIRECTIONS, Game, TIME_LIMIT, EXIT_DURATION, BUMP_DURATION, time_grade
from progress import Progress

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1040, 760
BG = '#F4F3ED'
INK = '#223F38'
MUTED = '#718179'
GREEN = '#28765C'
LINE = '#DFE5DC'
COLORS = {'U': '#28765C', 'D': '#D5984C', 'L': '#6683A5', 'R': '#9A7594'}


class App:
    def __init__(self, save_path=Path.home() / ".arrow_by_arrow" / "progress.json"):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('一箭又一箭 · Arrow by Arrow')
        self.clock = pygame.time.Clock()
        self.game = Game(LEVELS, progress=Progress(len(LEVELS), save_path))
        self.running = True
        font_file = ROOT / 'assets' / 'NotoSansCJKsc-Regular.otf'
        self.font_path = str(font_file) if font_file.exists() else pygame.font.match_font(
            'microsoftyahei,simhei,pingfangsc,notosanscjksc,wenquanyizenhei')
        if not self.font_path:
            raise RuntimeError('缺少中文字体，请保留 assets 文件夹或安装中文字体。')
        self.fonts = {}
        self.buttons = {}
        self.board_rect = pygame.Rect(64, 190, 540, 480)
        self.cell = 80
        self.notice = '点击箭头，让通路逐渐打开。'

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(self.font_path, size)
        return self.fonts[size]

    def text(self, value, pos, size=20, color=INK, center=False):
        surf = self.font(size).render(str(value), True, color)
        rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        self.screen.blit(surf, rect)
        return rect

    def panel(self, rect, color='white', border=None, radius=20):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=radius)

    def button(self, key, label, rect, primary=False):
        rect = pygame.Rect(rect)
        self.buttons[key] = rect
        hover = rect.collidepoint(pygame.mouse.get_pos())
        color = ('#205F4B' if hover else GREEN) if primary else ('#E0E8DF' if hover else '#EAF0E7')
        self.panel(rect, color, radius=12)
        self.text(label, rect.center, 19, 'white' if primary else INK, True)

    def arrow(self, center, direction, color, length=30, width=5):
        dr, dc = DIRECTIONS[direction]
        x, y = center
        ux, uy = dc, dr
        px, py = -uy, ux
        start = (x-ux*length/2, y-uy*length/2)
        tip = (x+ux*length/2, y+uy*length/2)
        pygame.draw.line(self.screen, color, start, tip, width)
        for sign in [-1, 1]:
            end = (tip[0]-ux*length*.34+sign*px*length*.29,
                   tip[1]-uy*length*.34+sign*py*length*.29)
            pygame.draw.line(self.screen, color, tip, end, width)

    def geometry(self):
        n, m = len(self.game.board), len(self.game.board[0])
        self.cell = min(78, 460//max(n, m))
        w, h = m*self.cell, n*self.cell
        self.board_rect = pygame.Rect(70+(540-w)//2, 195+(475-h)//2, w, h)

    def cell_center(self, row, col):
        return (self.board_rect.x+(col+.5)*self.cell,
                self.board_rect.y+(row+.5)*self.cell)

    def start(self, index=0):
        if not self.game.start(index):
            return
        self.game.state = 'READY'
        self.geometry()
        self.notice = '点击箭头，让通路逐渐打开。'

    def home_button(self, key, label, y):
        """主按钮更大，悬停时以绿色填充、描边和箭头强调。"""
        width, height = (360, 78) if key == 'start' else (280, 58)
        rect = pygame.Rect((WIDTH-width)//2, y, width, height)
        self.buttons[key] = rect
        hover = rect.collidepoint(pygame.mouse.get_pos())
        if hover:
            self.panel(rect.inflate(10, 10), '#D5E5D7', radius=19)
        self.panel(rect, GREEN if hover else '#E5EBE1',
                   '#205F4B' if hover else '#CFDACD', radius=14)
        self.text(label, rect.center, 27 if key == 'start' else 21, 'white' if hover else INK, True)
        if hover:
            self.arrow((rect.right-33, rect.centery), 'R', 'white', 18, 3)

    def draw_menu(self):
        # 装饰直接画在背景上，不使用独立卡片；中间留白保证阅读。
        motifs = [(116,154,'U',38), (230,273,'R',30), (106,478,'L',46),
                  (229,625,'D',34), (888,135,'R',44), (805,307,'D',32),
                  (932,458,'U',42), (835,647,'L',34)]
        for x,y,d,length in motifs:
            self.arrow((x,y), d, '#DEE5DA', length, 4)
        for x,y in [(178,372),(862,535),(270,126),(939,276),(117,649),(774,184)]:
            pygame.draw.circle(self.screen, '#E0E6DC', (x,y), 3)
        cx = WIDTH//2
        self.text('ARROW BY ARROW', (cx,89), 15, GREEN, True)
        self.text('观察方向，找到出口。', (cx,146), 21, MUTED, True)
        self.text('一箭又一箭', (cx,221), 64, INK, True)
        self.text('一场关于顺序的小小解谜', (cx,292), 23, GREEN, True)
        self.home_button('start', '开始游戏', 383)
        self.home_button('select', '选择关卡', 485)
        self.text('从第一关开始，或选择已解锁关卡刷新成绩。', (cx,614), 16, MUTED, True)
        if self.game.progress.message:
            self.text(self.game.progress.message, (cx,730), 16, '#B95D43', True)

    def draw_ready(self):
        cx = WIDTH//2
        self.text('准备好了吗？', (cx,121), 22, GREEN, True)
        self.text(f'第 {self.game.level_index+1} 关 · {LEVELS[self.game.level_index]["name"]}',
                  (cx,185), 38, INK, True)
        self.panel((230,249,580,260), 'white', LINE, 24)
        for i, line in enumerate(['点击前方畅通的箭头，让它飞出棋盘。',
                                  '每关限时 35 秒，拥有 3 次失误机会。',
                                  '获得 A 或 B，解锁下一关。']):
            self.text(line, (cx,291+i*43), 21, INK, True)
        self.text('A ≤15秒   /   B ≤25秒   /   C ≤35秒', (cx,443), 21, GREEN, True)
        self.text('超过 35 秒或失误机会用尽，本关失败。', (cx,483), 17, MUTED, True)
        self.button('begin', '开始挑战', (350,550,340,64), True)
        self.text('点击“开始挑战”后计时，现在可放心阅读规则。', (cx,645), 17, MUTED, True)
        self.button('select', '返回选关', (64, 40, 140,44))

    def draw_selection(self):
        self.text('ARROW / SELECT', (64, 39), 16, GREEN)
        self.text('选择关卡', (60, 82), 49)
        self.text('选择关卡，挑战更好的自己。', (64, 158), 21, MUTED)
        self.text('每关 35 秒 · A ≤15秒 / B ≤25秒 / C ≤35秒', (64, 213), 19, GREEN)
        self.text('前一关达到 A 或 B，即可永久解锁下一关。', (64, 248), 19, MUTED)
        for i, level in enumerate(LEVELS):
            x = 64 + i*310
            unlocked = self.game.progress.unlocked(i)
            self.panel((x, 311, 290, 279), 'white' if unlocked else '#E7EAE2', LINE)
            self.text(f'关卡 {i+1:02d}', (x+23, 333), 17, GREEN if unlocked else MUTED)
            self.text(level['name'], (x+23, 368), 28)
            best = self.game.progress.best[i]
            if best is not None:
                self.text(f'最佳 {time_grade(best)}  ·  {best:.2f} 秒', (x+23, 429), 22, GREEN)
            else:
                self.text('尚未挑战' if unlocked else '尚未解锁', (x+23, 429), 22, MUTED)
            if unlocked:
                self.text('反复挑战，刷新最佳成绩', (x+23, 471), 16, MUTED)
                self.button(f'level_{i}', '再次挑战' if best is not None else '开始挑战',
                            (x+23, 517, 244, 48), True)
            else:
                self.text(f'需要第 {i} 关获得 A 或 B', (x+23, 471), 16, MUTED)
                self.panel((x+23, 517, 244, 48), '#DADFD5', radius=12)
                self.text('未解锁', (x+145, 541), 19, MUTED, True)
        self.button('menu', '返回首页', (64, 628, 240, 51))
        self.text('已解锁关卡始终可选，较低成绩不会覆盖最佳成绩。', (333, 642), 17, MUTED)
        if self.game.progress.message:
            self.text(self.game.progress.message, (64, 706), 17, '#B95D43')

    def draw_board(self):
        self.panel((48,171,586,520), 'white', LINE, 26)
        hint = self.game.hint
        animation = self.game.animation
        for r,row in enumerate(self.game.board):
            for c,d in enumerate(row):
                x,y = self.cell_center(r,c)
                rect = pygame.Rect(int(x-self.cell/2+5), int(y-self.cell/2+5), self.cell-10, self.cell-10)
                if d is None:
                    pygame.draw.circle(self.screen, '#E5E9E2', (round(x),round(y)), 3)
                    continue
                fill = '#F0F3ED'
                if hint == (r,c): fill = '#D4EBC0'
                if rect.collidepoint(pygame.mouse.get_pos()) and not animation: fill = '#E4EADF'
                if animation and (r,c)==(animation.row,animation.col) and animation.kind=='bump':
                    fill = '#FCE1D7'
                self.panel(rect, fill, radius=13)
                if animation and (r,c)==(animation.row,animation.col): continue
                self.arrow((x,y), d, COLORS[d], self.cell*.39, 5)
        if animation:
            x,y=self.cell_center(animation.row,animation.col)
            dr,dc=DIRECTIONS[animation.direction]
            if animation.kind=='exit':
                t=min(1,animation.elapsed/EXIT_DURATION)
                if dc==1: distance=self.board_rect.right-x+self.cell
                elif dc==-1: distance=x-self.board_rect.left+self.cell
                elif dr==1: distance=self.board_rect.bottom-y+self.cell
                else: distance=y-self.board_rect.top+self.cell
                offset=distance*t*t
                color=COLORS[animation.direction]
            else:
                t=min(1,animation.elapsed/BUMP_DURATION)
                offset=math.sin(t*math.pi)*self.cell*.17
                color='#CE684D'
            old_clip=self.screen.get_clip()
            self.screen.set_clip(self.board_rect)
            self.arrow((x+dc*offset,y+dr*offset),animation.direction,color,self.cell*.39,5)
            self.screen.set_clip(old_clip)

    def draw_playing(self):
        g=self.game
        level=LEVELS[g.level_index]
        self.text('一箭又一箭', (48,31), 31)
        self.text('ARROW BY ARROW', (50,80), 12, MUTED)
        self.text(f'关卡 {g.level_index+1:02d} / {len(LEVELS):02d}', (48,124), 20, GREEN)
        self.text(level['name'], (225,124), 20)
        self.button('menu','返回首页',(852,40,140,44))
        self.draw_board()
        self.panel((662,171,330,201), 'white', LINE)
        self.text('本关进度', (686,192), 17, MUTED)
        self.text(f'{g.remaining:02d}', (684,221), 43)
        self.text('剩余箭头', (771,246), 18, MUTED)
        total=sum(v is not None for row in level['board'] for v in row)
        self.panel((688,302,274,7), '#E8EDE5',radius=3)
        progress=round(274*(1-g.remaining/total))
        if progress: self.panel((688,302,progress,7),GREEN,radius=3)
        self.text(f'剩余失误机会   {g.mistakes} / {g.max_mistakes}',(686,325),18,
                  '#B95D43' if g.mistakes<=1 else GREEN)
        self.panel((662,392,330,135), '#E7EBDD')
        time_color = '#B95D43' if g.elapsed > 25 else GREEN
        self.text(f'用时 {g.elapsed:.2f} 秒', (686,409), 24, time_color)
        self.text(f'剩余 {max(0, TIME_LIMIT-g.elapsed):.2f} 秒', (686,450), 18, time_color)
        self.text('A ≤15s  /  B ≤25s  /  C ≤35s', (686,487), 16, MUTED)
        self.button('hint','提示  H',(662,550,156,49))
        self.button('restart','重新开始  R',(834,550,158,49))
        self.text('提示不会扣除失误机会', (662,616), 16, MUTED)
        self.text(self.notice,(50,713),18,'#B95D43' if g.animation and g.animation.kind=='bump' else MUTED)

    def draw_result(self):
        self.draw_playing()
        shade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        shade.fill((28,48,41,145))
        self.screen.blit(shade,(0,0))
        self.buttons.clear()
        self.panel((280,198,480,354),'#FAFBF6',radius=28)
        state=self.game.state
        won=state!='GAME_OVER'
        title={'LEVEL_CLEAR':'通路已打开！','ALL_CLEAR':'全部通关！','GAME_OVER':'再观察一次吧'}[state]
        self.text(f'评价 {self.game.grade}' if won else 'TRY AGAIN',(520,230),16,GREEN if won else '#B95D43',True)
        self.text(title,(520,291),36,INK,True)
        subtitle=(f'已完成全部 {len(LEVELS)} 个关卡。' if state=='ALL_CLEAR' else
                  ('达到 B 及以上，已解锁下一关。' if self.game.grade in ('A','B') else
                   '本次为 C，重试达到 B 可进入下一关。') if won else '超过 35 秒，时间已用完。' if self.game.failure_reason == 'timeout' else
                  '失误机会已用完，重新挑战本关。')
        self.text(subtitle,(520,350),19,MUTED,True)
        self.text(f'本关用时 {self.game.elapsed:.2f} 秒  ·  提示 {self.game.used_hints} 次',(520,385),16,MUTED,True)
        label='下一关' if state=='LEVEL_CLEAR' and self.game.grade in ('A','B') else '再次挑战' if won else '重新挑战'
        self.button('continue',label,(305,432,138,55),True)
        self.button('restart','重试本关',(451,432,138,55))
        self.button('select','选择关卡',(597,432,138,55))
        if self.game.progress.message:
            self.text(self.game.progress.message, (520,517), 15, '#B95D43', True)

    def draw(self):
        self.screen.fill(BG)
        self.buttons.clear()
        if self.game.state=='MENU': self.draw_menu()
        elif self.game.state=='SELECT': self.draw_selection()
        elif self.game.state=='READY': self.draw_ready()
        elif self.game.state=='PLAYING': self.draw_playing()
        else: self.draw_result()
        pygame.display.flip()

    def action(self, key):
        g=self.game
        if key=='start': self.start()
        elif key=='begin' and g.state=='READY':
            g.state='PLAYING'
            self.clock.tick()  # 清除说明页的帧间隔，计时从确认后开始。
        elif key=='select':
            g.menu()
            g.state='SELECT'
        elif key.startswith('level_'):
            self.start(int(key.split('_')[1]))
        elif key=='menu': g.menu()
        elif key=='restart':
            self.start(g.level_index)
        elif key=='hint':
            g.show_hint()
        elif key=='continue':
            if g.state=='LEVEL_CLEAR' and g.grade in ('A','B'): self.start(g.level_index+1)
            elif g.state in ('LEVEL_CLEAR','ALL_CLEAR','GAME_OVER'): self.start(g.level_index)

    def handle_event(self,event):
        if event.type==pygame.QUIT:
            self.running=False
        elif event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: self.game.menu()
            elif event.key==pygame.K_r and self.game.state=='PLAYING': self.action('restart')
            elif event.key==pygame.K_h and self.game.state=='PLAYING': self.action('hint')
            elif event.key==pygame.K_RETURN:
                self.action('start' if self.game.state=='MENU' else 'begin' if self.game.state=='READY' else 'continue')
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for key,rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    self.action(key)
                    return
            if self.game.state=='PLAYING' and self.board_rect.collidepoint(event.pos):
                c=int((event.pos[0]-self.board_rect.x)//self.cell)
                r=int((event.pos[1]-self.board_rect.y)//self.cell)
                result=self.game.click(r,c)
                if result=='bump': self.notice='前方有阻挡！先移除挡路的箭头。'
                elif result=='exit': self.notice='通路畅通，箭头飞出！'

    def run(self):
        self.draw()
        while self.running:
            # 不截断 dt：低帧率、窗口拖动等期间也必须累计实际经过时间。
            dt=self.clock.tick(60)/1000
            self.game.update(dt)
            self.draw()  # 超时后先更新结果页按钮，再处理鼠标事件。
            for event in pygame.event.get():
                self.handle_event(event)
                # 同一帧内状态变化后，立即更新按钮集合，避免旧按钮响应。
                if event.type in (pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN): self.draw()
            self.draw()
        pygame.quit()


if __name__=='__main__':
    App().run()
