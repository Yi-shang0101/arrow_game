"""使用 SDL dummy 驱动验证真实事件处理与渲染，不需要桌面。"""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
import pygame
from main import App
from logic import can_exit, solve
from levels import LEVELS

class UITests(unittest.TestCase):
    def setUp(self):
        self.app=App(save_path=None)
        self.app.draw()

    def click(self,pos):
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))
        self.app.draw()

    def button(self,key): self.click(self.app.buttons[key].center)

    def finish_animation(self):
        for _ in range(40):
            self.app.game.update(1/60)
            self.app.draw()

    def tearDown(self): pygame.quit()

    def test_mouse_three_level_playthrough(self):
        self.button('start')
        for i,level in enumerate(LEVELS):
            self.assertEqual(self.app.game.level_index,i)
            for r,c in solve(level['board']):
                self.click(self.app.cell_center(r,c))
                self.finish_animation()
            self.assertEqual(self.app.game.state,'ALL_CLEAR' if i==2 else 'LEVEL_CLEAR')
            self.button('continue')
        self.assertEqual(self.app.game.level_index,2)
        self.assertEqual(self.app.game.state,'PLAYING')

    def test_fail_restart_outside_hint_and_home(self):
        self.button('start')
        g=self.app.game
        self.click((35,200))
        self.assertEqual(g.mistakes,3)
        self.button('hint')
        self.assertIsNotNone(g.hint)
        r,c=next((r,c) for r,row in enumerate(g.board) for c,d in enumerate(row)
                 if d and not can_exit(g.board,r,c))
        for i in range(3):
            self.click(self.app.cell_center(r,c))
            self.click(self.app.cell_center(r,c))
            self.assertEqual(g.mistakes,2-i)
            self.finish_animation()
        self.assertEqual(g.state,'GAME_OVER')
        self.button('continue')
        self.assertEqual(g.board,LEVELS[0]['board'])
        self.assertEqual(g.mistakes,3)
        r,c=solve(g.board)[0]
        self.click(self.app.cell_center(r,c))
        self.button('restart')
        self.finish_animation()
        self.assertEqual(g.board,LEVELS[0]['board'])
        self.button('menu')
        self.assertEqual(g.state,'MENU')

    def test_timeout_result_restart_and_grade_render(self):
        self.button('start')
        self.app.game.update(35.001)
        self.app.draw()
        self.assertEqual(self.app.game.failure_reason,'timeout')
        self.assertIn('continue',self.app.buttons)
        self.button('continue')
        self.assertEqual(self.app.game.elapsed,0)
        for r,c in solve(self.app.game.board):
            self.click(self.app.cell_center(r,c))
            self.app.game.update(.25)
            self.app.draw()
        self.assertEqual(self.app.game.grade,'A')
        self.assertIn('continue',self.app.buttons)

    def test_home_selection_and_C_retry(self):
        self.assertIn('select',self.app.buttons)
        self.assertNotIn('level_0',self.app.buttons)
        self.button('select')
        self.assertIn('level_0',self.app.buttons)
        self.assertNotIn('level_1',self.app.buttons)
        self.app.action('level_1')
        self.assertEqual(self.app.game.state,'SELECT')
        self.button('level_0')
        self.app.game.update(26)
        for r,c in solve(self.app.game.board):
            self.click(self.app.cell_center(r,c))
            self.app.game.update(.25);self.app.draw()
        self.assertEqual(self.app.game.grade,'C')
        self.button('continue')
        self.assertEqual(self.app.game.level_index,0)
        for r,c in solve(self.app.game.board):
            self.click(self.app.cell_center(r,c))
            self.app.game.update(.25);self.app.draw()
        self.button('select')
        self.assertIn('level_1',self.app.buttons)
        self.assertNotIn('level_2',self.app.buttons)
        self.button('level_1')
        self.assertEqual(self.app.game.level_index,1)
        self.button('menu');self.button('select');self.button('level_0')
        self.assertEqual(self.app.game.level_index,0)

    def test_home_selection_back_and_timer_stopped(self):
        self.assertEqual(self.app.game.state,'MENU')
        self.button('select')
        self.assertEqual(self.app.game.state,'SELECT')
        self.app.game.update(40)
        self.assertEqual(self.app.game.elapsed,0)
        self.button('menu')
        self.assertEqual(self.app.game.state,'MENU')
        self.assertIn('start',self.app.buttons)
        self.assertNotIn('level_0',self.app.buttons)
        self.button('select')
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.app.draw()
        self.assertEqual(self.app.game.state,'MENU')

if __name__=='__main__': unittest.main()
