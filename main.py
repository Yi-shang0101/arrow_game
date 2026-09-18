"""一箭又一箭：Pygame 界面。运行 python main.py。"""
import math
import os
import random
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

THEMES = {
    'day': {
        'label': '白天模式',
        'bg': '#F4F3ED', 'ink': '#223F38', 'muted': '#718179',
        'green': '#28765C', 'line': '#DFE5DC', 'panel': '#FFFFFF',
        'soft': '#EAF0E7', 'soft_hover': '#E0E8DF', 'alt': '#E7EBDD',
        'button': '#E5EBE1', 'button_border': '#CFDACD',
        'button_hover': '#D5E5D7', 'primary_hover': '#205F4B',
        'cell': '#F0F3ED', 'empty': '#E5E9E2', 'cell_hover': '#E4EADF',
        'hint': '#D4EBC0', 'danger': '#B95D43', 'danger_fill': '#FCE1D7',
        'disabled': '#DADFD5', 'track': '#E8EDE5', 'slider_track': '#D5DFD4',
        'slider_fill': '#28765C', 'slider_knob': '#205F4B',
        'motif': '#92B49D', 'dot': '#B2C7AF',
        'arrows': {'U': '#28765C', 'D': '#D5984C', 'L': '#6683A5', 'R': '#9A7594'},
    },
    'eye': {
        'label': '护眼模式',
        'bg': '#EEF4E8', 'ink': '#29473B', 'muted': '#6D8175',
        'green': '#43825D', 'line': '#D3E1D1', 'panel': '#F9FCF5',
        'soft': '#E1ECDD', 'soft_hover': '#D5E8D6', 'alt': '#E3EEE0',
        'button': '#E4EEE1', 'button_border': '#C9DCC8',
        'button_hover': '#D5E8D6', 'primary_hover': '#36714F',
        'cell': '#ECF4E9', 'empty': '#DDE9DC', 'cell_hover': '#DCEBDF',
        'hint': '#C9E6C4', 'danger': '#B4634A', 'danger_fill': '#F7DCD1',
        'disabled': '#D6E1D3', 'track': '#E1EBDD', 'slider_track': '#CFDFCF',
        'slider_fill': '#43825D', 'slider_knob': '#36714F',
        'motif': '#8DB99B', 'dot': '#A9C8A7',
        'arrows': {'U': '#397A5A', 'D': '#C58943', 'L': '#5D7E9A', 'R': '#906E87'},
    },
    'night': {
        'label': '夜间模式',
        'bg': '#182A28', 'ink': '#F0F4E8', 'muted': '#B2C6BC',
        'green': '#75D2AA', 'line': '#3B5750', 'panel': '#223633',
        'soft': '#2C4641', 'soft_hover': '#35554C', 'alt': '#2B413C',
        'button': '#29433E', 'button_border': '#567A6A',
        'button_hover': '#3D6555', 'primary_hover': '#4EAE89',
        'cell': '#2A403C', 'empty': '#35504A', 'cell_hover': '#38544C',
        'hint': '#4C7557', 'danger': '#F1A27F', 'danger_fill': '#6B4138',
        'disabled': '#314741', 'track': '#314A44', 'slider_track': '#405D54',
        'slider_fill': '#75D2AA', 'slider_knob': '#BFE7CE',
        'motif': '#5C9E83', 'dot': '#6DAA8A',
        'arrows': {'U': '#70D6AE', 'D': '#E8B968', 'L': '#9AB6D8', 'R': '#C89CC3'},
    },
}
THEME_OPTIONS = (('day', '白天模式'), ('eye', '护眼模式'), ('night', '夜间模式'))


class AudioManager:
    """集中管理音乐和音效；没有可用音频设备时安全降级为静音。"""
    MUSIC = {'menu': '主菜单音乐.mp3', 'game': '进行游戏音乐.mp3'}
    EFFECTS = {
        'countdown': '倒计时.wav',
        'failure': '游戏失败.wav',
        'failure_1': '游戏失败1.wav',
        'failure_2': '游戏失败2.wav',
        'failure_3': '游戏失败3.wav',
        'success': '游戏成功.wav',
        'blocked': '箭头被阻挡.wav',
        'fly': '箭头飞出.wav',
        'button': '点击按钮.wav',
    }
    FAILURE_KEYS = ('failure', 'failure_1', 'failure_2', 'failure_3')
    NEW_FAILURE_KEYS = ('failure_1', 'failure_2', 'failure_3')

    def __init__(self, audio_dir):
        self.audio_dir = Path(audio_dir)
        self.enabled = False
        self.current_music = None
        self.countdown_channel = None
        self.result_channel = None
        self.countdown_bus = None
        self.result_bus = None
        self.effects = {}
        self.last_failure_key = None
        self.music_volume = 0.8
        self.effect_volume = 0.8
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(8)
            # 0/1 专用于倒计时和结果音效，普通按钮音效不会复用这两个通道。
            pygame.mixer.set_reserved(2)
            self.countdown_bus = pygame.mixer.Channel(0)
            self.result_bus = pygame.mixer.Channel(1)
            for key, filename in self.EFFECTS.items():
                path = self.audio_dir / filename
                if path.exists():
                    self.effects[key] = pygame.mixer.Sound(str(path))
            self.enabled = bool(self.effects)
            if self.enabled:
                self.set_effect_volume(self.effect_volume)
        except (pygame.error, OSError):
            self.enabled = False
            self.effects.clear()
            self.countdown_bus = None
            self.result_bus = None

    def play_music(self, key):
        if not self.enabled or key not in self.MUSIC:
            return
        path = self.audio_dir / self.MUSIC[key]
        if not path.exists():
            return
        if self.current_music == key and pygame.mixer.music.get_busy():
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume((0.28 if key == 'menu' else 0.24) * self.music_volume)
            pygame.mixer.music.play(-1)
            self.current_music = key
        except pygame.error:
            self.current_music = None

    @staticmethod
    def _volume(value):
        return max(0.0, min(1.0, float(value)))

    def set_music_volume(self, value):
        """设置音乐百分比，并立即作用于当前循环音乐。"""
        self.music_volume = self._volume(value)
        if self.enabled and self.current_music:
            try:
                base = 0.28 if self.current_music == 'menu' else 0.24
                pygame.mixer.music.set_volume(base * self.music_volume)
            except pygame.error:
                pass

    def set_effect_volume(self, value):
        """设置音效百分比，并更新已加载的所有音效。"""
        self.effect_volume = self._volume(value)
        for key, sound in self.effects.items():
            try:
                base = 0.42 if key == 'countdown' else 0.62
                sound.set_volume(base * self.effect_volume)
            except pygame.error:
                pass

    def play_effect(self, key):
        if self.enabled and key in self.effects:
            try:
                if (key == 'success' or key in self.FAILURE_KEYS) and self.result_bus is not None:
                    self.result_bus.play(self.effects[key])
                    self.result_channel = self.result_bus
                else:
                    self.effects[key].play()
            except pygame.error:
                pass

    def play_failure(self, new_only=False):
        """随机播放失败音效；退出游戏时只从本次新增的三条中选择。"""
        candidates = self.NEW_FAILURE_KEYS if new_only else self.FAILURE_KEYS
        key = random.choice(candidates)
        self.last_failure_key = key
        self.play_effect(key)
        return self.result_channel

    def stop_result(self):
        """立即停止通关/失败结果音效，供结果页按钮切换前调用。"""
        if self.result_channel is not None:
            try:
                self.result_channel.stop()
            except pygame.error:
                pass
            self.result_channel = None

    def start_countdown(self):
        self.stop_countdown()
        if self.enabled and 'countdown' in self.effects:
            try:
                if self.countdown_bus is not None:
                    self.countdown_bus.play(self.effects['countdown'])
                    self.countdown_channel = self.countdown_bus
                else:
                    self.countdown_channel = None
            except pygame.error:
                self.countdown_channel = None

    def stop_countdown(self):
        if self.countdown_channel is not None:
            try:
                self.countdown_channel.stop()
            except pygame.error:
                pass
            self.countdown_channel = None

    def stop_music(self):
        if self.enabled:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass
        self.current_music = None


class App:
    def __init__(self, save_path=Path.home() / ".arrow_by_arrow" / "progress.json"):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('一箭又一箭 · Arrow by Arrow')
        self.clock = pygame.time.Clock()
        self.game = Game(LEVELS, progress=Progress(len(LEVELS), save_path))
        self.audio = AudioManager(ROOT / 'assets' / 'audio')
        self._audio_state = None
        self.running = True
        self.quit_requested = False
        self.quit_channel = None
        self.quit_deadline = 0
        font_file = ROOT / 'assets' / 'NotoSansCJKsc-Regular.otf'
        self.font_path = str(font_file) if font_file.exists() else pygame.font.match_font(
            'microsoftyahei,simhei,pingfangsc,notosanscjksc,wenquanyizenhei')
        if not self.font_path:
            raise RuntimeError('缺少中文字体，请保留 assets 文件夹或安装中文字体。')
        self.fonts = {}
        self.buttons = {}
        self.sliders = {}
        self.dragging_slider = None
        self.theme_mode = 'day'
        self.board_rect = pygame.Rect(64, 190, 540, 480)
        self.cell = 80
        self.notice = '点击箭头，让通路逐渐打开。'

    def sync_audio(self):
        state = self.game.state
        if state == self._audio_state:
            return
        self._audio_state = state
        if state in ('MENU', 'SELECT', 'READY', 'SETTINGS'):
            self.audio.stop_countdown()
            self.audio.play_music('menu')
        elif state == 'PLAYING':
            self.audio.play_music('game')
            self.audio.start_countdown()
        elif state in ('LEVEL_CLEAR', 'ALL_CLEAR'):
            self.audio.stop_countdown()
            self.audio.play_effect('success')
            self.audio.play_music('menu')
        elif state == 'GAME_OVER':
            self.audio.stop_countdown()
            self.audio.play_failure()
            self.audio.play_music('menu')

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(self.font_path, size)
        return self.fonts[size]

    def theme_color(self, value):
        """把旧页面使用的颜色常量映射到当前主题，保持三种模式整体一致。"""
        palette = THEMES[self.theme_mode]
        aliases = {
            BG: 'bg', INK: 'ink', MUTED: 'muted', GREEN: 'green', LINE: 'line',
            'white': 'panel', '#FAFBF6': 'panel', '#EAF0E7': 'soft',
            '#E0E8DF': 'soft_hover', '#E5EBE1': 'button', '#CFDACD': 'button_border',
            '#205F4B': 'primary_hover', '#D5E5D7': 'button_hover', '#E7EBDD': 'alt',
            '#E7EAE2': 'alt', '#E8EDE5': 'track', '#F0F3ED': 'cell',
            '#E5E9E2': 'empty', '#D4EBC0': 'hint', '#E4EADF': 'cell_hover',
            '#FCE1D7': 'danger_fill', '#B95D43': 'danger', '#DADFD5': 'disabled',
            '#92B49D': 'motif', '#B2C7AF': 'dot',
        }
        if value in COLORS.values():
            for direction, base in COLORS.items():
                if value == base:
                    return palette['arrows'][direction]
        key = aliases.get(value)
        return palette[key] if key else value

    def text(self, value, pos, size=20, color=INK, center=False):
        render_color = '#FFFFFF' if color == 'white' else self.theme_color(color)
        surf = self.font(size).render(str(value), True, render_color)
        rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        self.screen.blit(surf, rect)
        return rect

    def panel(self, rect, color='white', border=None, radius=20):
        pygame.draw.rect(self.screen, self.theme_color(color), rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.screen, self.theme_color(border), rect, 1, border_radius=radius)

    def button(self, key, label, rect, primary=False):
        rect = pygame.Rect(rect)
        self.buttons[key] = rect
        hover = rect.collidepoint(pygame.mouse.get_pos())
        color = ('#205F4B' if hover else GREEN) if primary else ('#E0E8DF' if hover else '#EAF0E7')
        self.panel(rect, color, radius=12)
        self.text(label, rect.center, 19, 'white' if primary else INK, True)

    def draw_slider(self, key, label, value, y):
        """绘制并注册一个可拖动的音量滑动条。"""
        self.text(label, (210, y - 12), 21, INK)
        rect = pygame.Rect(365, y, 450, 10)
        self.sliders[key] = rect
        self.panel(rect, THEMES[self.theme_mode]['slider_track'], radius=5)
        fill = pygame.Rect(rect.x, rect.y, round(rect.width * value), rect.height)
        if fill.width:
            self.panel(fill, THEMES[self.theme_mode]['slider_fill'], radius=5)
        knob_x = rect.x + round(rect.width * value)
        pygame.draw.circle(self.screen, THEMES[self.theme_mode]['slider_knob'], (knob_x, rect.centery), 12)
        self.text(f'{round(value * 100):d}%', (845, y - 13), 19, GREEN)

    def draw_theme_button(self, key, label, rect):
        rect = pygame.Rect(rect)
        self.buttons[f'theme_{key}'] = rect
        palette = THEMES[self.theme_mode]
        selected = self.theme_mode == key
        hover = rect.collidepoint(pygame.mouse.get_pos())
        if hover and not selected:
            self.panel(rect.inflate(6, 6), palette['soft_hover'], radius=15)
        color = palette['green'] if selected else palette['button']
        border = palette['green'] if selected else palette['button_border']
        self.panel(rect, color, border, radius=12)
        self.text(label, rect.center, 18, palette['bg'] if selected else INK, True)

    def arrow(self, center, direction, color, length=30, width=5):
        dr, dc = DIRECTIONS[direction]
        x, y = center
        color = self.theme_color(color)
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
            self.arrow((x,y), d, '#92B49D', length, 5)
        for x,y in [(178,372),(862,535),(270,126),(939,276),(117,649),(774,184)]:
            pygame.draw.circle(self.screen, self.theme_color('#B2C7AF'), (x,y), 4)
        cx = WIDTH//2
        self.text('ARROW BY ARROW', (cx,89), 15, GREEN, True)
        self.text('观察方向，找到出口。', (cx,146), 21, MUTED, True)
        self.text('一箭又一箭', (cx,221), 64, INK, True)
        self.text('一场关于顺序的小小解谜', (cx,292), 23, GREEN, True)
        self.home_button('start', '开始游戏', 335)
        self.home_button('select', '选择关卡', 432)
        self.home_button('settings', '设置', 501)
        self.home_button('quit', '退出游戏', 570)
        self.text('从第一关开始，或选择已解锁关卡刷新成绩。', (cx,690), 16, MUTED, True)
        if self.game.progress.message:
            self.text(self.game.progress.message, (cx,730), 16, '#B95D43', True)

    def draw_settings(self):
        """设置页：音效/音乐音量滑动条与三种显示模式。"""
        self.text('ARROW / SETTINGS', (64, 39), 16, GREEN)
        self.text('设置', (60, 82), 49)
        self.text('调整音量和显示模式，修改会立即生效。', (64, 158), 21, MUTED)
        self.panel((150, 195, 740, 420), 'white', LINE, 26)
        self.text('音量', (210, 238), 24, GREEN)
        self.draw_slider('effect_volume', '音效音量', self.audio.effect_volume, 302)
        self.draw_slider('music_volume', '音乐音量', self.audio.music_volume, 382)
        self.text('显示模式', (210, 463), 24, GREEN)
        for index, (key, label) in enumerate(THEME_OPTIONS):
            self.draw_theme_button(key, label, (210 + index * 205, 500, 180, 54))
        current = THEMES[self.theme_mode]['label']
        self.text(f'当前模式：{current}', (520, 584), 17, MUTED, True)
        self.button('menu', '返回首页', (64, 672, 180, 48))
        self.text('音量范围 0%—100%，可直接拖动滑块。', (300, 695), 16, MUTED)

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
        self.button('menu', '返回首页', (836, 40, 140,44))

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
                    pygame.draw.circle(self.screen, self.theme_color('#E5E9E2'), (round(x),round(y)), 3)
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
        self.panel((280,180,480,395),'#FAFBF6',radius=28)
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
        self.button('menu','返回首页',(451,502,138,50))
        if self.game.progress.message:
            self.text(self.game.progress.message, (520,570), 15, '#B95D43', True)

    def draw(self):
        self.sync_audio()
        self.screen.fill(self.theme_color(BG))
        self.buttons.clear()
        self.sliders.clear()
        if self.game.state=='MENU': self.draw_menu()
        elif self.game.state=='SELECT': self.draw_selection()
        elif self.game.state=='READY': self.draw_ready()
        elif self.game.state=='SETTINGS': self.draw_settings()
        elif self.game.state=='PLAYING': self.draw_playing()
        else: self.draw_result()
        pygame.display.flip()

    def set_slider_value(self, key, x):
        rect = self.sliders.get(key)
        if rect is None:
            return
        value = max(0.0, min(1.0, (x - rect.left) / rect.width))
        if key == 'effect_volume':
            self.audio.set_effect_volume(value)
        elif key == 'music_volume':
            self.audio.set_music_volume(value)

    def set_theme(self, key):
        if key in THEMES:
            self.theme_mode = key

    def action(self, key):
        g=self.game
        if key in ('continue', 'restart', 'select', 'menu') and g.state in ('LEVEL_CLEAR', 'ALL_CLEAR', 'GAME_OVER'):
            self.audio.stop_result()
        if key=='start': self.start()
        elif key=='settings':
            g.menu()
            g.state='SETTINGS'
        elif key=='quit':
            # 退出前播放一条本次新增的短失败音效，并留出播放时间再关闭窗口。
            if self.quit_requested:
                return
            self.audio.stop_countdown()
            self.audio.stop_result()
            self.audio.stop_music()
            self.quit_channel = self.audio.play_failure(new_only=True)
            if self.audio.enabled and self.quit_channel is not None:
                self.quit_requested = True
                self.quit_deadline = pygame.time.get_ticks() + 1500
            else:
                self.running = False
        elif key=='begin' and g.state=='READY':
            g.state='PLAYING'
            self.clock.tick()  # 清除说明页的帧间隔，计时从确认后开始。
        elif key=='select':
            g.menu()
            g.state='SELECT'
        elif key.startswith('level_'):
            self.start(int(key.split('_')[1]))
        elif key=='menu': g.menu()
        elif key.startswith('theme_') and g.state == 'SETTINGS':
            self.set_theme(key.split('_', 1)[1])
        elif key=='restart':
            self.start(g.level_index)
        elif key=='hint':
            g.show_hint()
        elif key=='continue':
            if g.state=='LEVEL_CLEAR' and g.grade in ('A','B'): self.start(g.level_index+1)
            elif g.state in ('LEVEL_CLEAR','ALL_CLEAR','GAME_OVER'): self.start(g.level_index)

    def handle_event(self,event):
        if event.type==pygame.QUIT:
            self.action('quit')
        elif event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: self.action('menu')
            elif event.key==pygame.K_r and self.game.state=='PLAYING': self.action('restart')
            elif event.key==pygame.K_h and self.game.state=='PLAYING': self.action('hint')
            elif event.key==pygame.K_RETURN:
                self.action('start' if self.game.state=='MENU' else 'begin' if self.game.state=='READY' else 'continue')
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for key,rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    if key in ('continue', 'restart', 'select', 'menu'):
                        self.audio.stop_result()
                    self.audio.play_effect('button')
                    self.action(key)
                    return
            if self.game.state=='SETTINGS':
                for key, rect in self.sliders.items():
                    if rect.inflate(20, 30).collidepoint(event.pos):
                        self.dragging_slider = key
                        self.set_slider_value(key, event.pos[0])
                        self.audio.play_effect('button')
                        return
            if self.game.state=='PLAYING' and self.board_rect.collidepoint(event.pos):
                c=int((event.pos[0]-self.board_rect.x)//self.cell)
                r=int((event.pos[1]-self.board_rect.y)//self.cell)
                result=self.game.click(r,c)
                if result=='bump':
                    self.audio.play_effect('blocked')
                    self.notice='前方有阻挡！先移除挡路的箭头。'
                elif result=='exit':
                    self.audio.play_effect('fly')
                    self.notice='通路畅通，箭头飞出！'
        elif event.type==pygame.MOUSEMOTION and self.dragging_slider:
            if event.buttons[0]:
                self.set_slider_value(self.dragging_slider, event.pos[0])
        elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
            self.dragging_slider = None

    def run(self):
        self.draw()
        while self.running:
            if self.quit_requested:
                if (self.quit_channel is None or not self.quit_channel.get_busy() or
                        pygame.time.get_ticks() >= self.quit_deadline):
                    self.running = False
                    break
                # 退出时只维持事件泵和音效，不再推进游戏逻辑或重绘页面。
                pygame.event.pump()
                self.clock.tick(60)
                continue
            # 不截断 dt：低帧率、窗口拖动等期间也必须累计实际经过时间。
            dt=self.clock.tick(60)/1000
            self.game.update(dt)
            self.draw()  # 超时后先更新结果页按钮，再处理鼠标事件。
            for event in pygame.event.get():
                self.handle_event(event)
                # 同一帧内状态变化后，立即更新按钮集合，避免旧按钮响应。
                if (event.type in (pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN)
                        and not self.quit_requested):
                    self.draw()
            if not self.quit_requested:
                self.draw()
        pygame.quit()


if __name__=='__main__':
    App().run()
