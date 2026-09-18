"""重现界面截图；从项目根目录运行 python docs/capture_demo.py。"""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from main import App
from logic import can_exit, solve

out=Path(__file__).resolve().parent
app=App(save_path=None)
def capture(name):
    app.draw()
    pygame.image.save(app.screen,str(out/name))
capture('01_menu.png')
app.start(0)
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
for r,c in solve(app.game.board):
    app.game.click(r,c)
    app.game.update(1)
capture('05_clear.png')
app.game.progress.record(1,10)
app.start(2)
capture('06_level3.png')
for r,c in solve(app.game.board):
    app.game.click(r,c)
    app.game.update(1)
capture('07_all_clear.png')
app.start(1)
app.game.update(35.01)
capture('08_timeout.png')
app.game.menu()
capture('09_selection.png')
pygame.quit()
print('Saved 9 screenshots')
