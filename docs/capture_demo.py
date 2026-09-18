"""重现界面截图；从项目根目录运行 python docs/capture_demo.py。"""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from main import App, MENU_MOTIFS
from logic import EXIT_DURATION, can_exit, solve

out=Path(__file__).resolve().parent
app=App(save_path=None)
def capture(name):
    app.draw()
    pygame.image.save(app.screen,str(out/name))
capture('01_menu.png')
x, y, _direction, _length = MENU_MOTIFS[0]
app.pointer_pos = (x, y)
app.launch_background_arrow(0)
app.update_background_animation(0.2)
capture('10_home_hover.png')
app.background_arrow_flight = None
app.start(0)
app.action('begin')
capture('02_game.png')
r,c=next((r,c) for r,row in enumerate(app.game.board) for c,d in enumerate(row)
         if d and not can_exit(app.game.board,r,c))
app.game.click(r,c)
app.notice='前方有阻挡！先移除挡路的箭头。'
app.game.update(.17)
capture('03_collision.png')
app.game.update(.5)
for _ in range(2):
    app.game.click(r,c)
    app.game.update(1)
capture('04_failure.png')
app.start(0)
app.action('begin')
for r,c in solve(app.game.board):
    app.game.click(r,c)
    app.game.update(EXIT_DURATION)
capture('05_clear.png')
app.start(1)
app.action('begin')
for r,c in solve(app.game.board):
    app.game.click(r,c)
    app.game.update(EXIT_DURATION)
app.start(2)
app.action('begin')
capture('06_level3.png')
for index in range(2, len(app.game.levels)):
    if index > 2:
        app.start(index)
        app.action('begin')
    for r,c in solve(app.game.board):
        app.game.click(r,c)
        app.game.update(EXIT_DURATION)
capture('07_all_clear.png')
app.start(1)
app.action('begin')
app.game.update(35.01)
capture('08_timeout.png')
app.action('select')
capture('09_selection.png')
app.start(0)
capture('11_rules.png')
app.action('settings')
capture('13_settings_day.png')
app.action('theme_night')
capture('14_settings_night.png')
pygame.quit()
print('Saved 13 screenshots')
