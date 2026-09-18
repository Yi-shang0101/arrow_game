import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from logic import Game
from progress import Progress

class ProgressTests(unittest.TestCase):
    def game(self, progress=None):
        return Game([{'board':[['U']]} for _ in range(3)], progress=progress)

    def clear(self, g, seconds):
        g.update(seconds-.25); g.click(0,0); g.update(.25)

    def test_initial_locks_and_start_guard(self):
        g=self.game()
        self.assertTrue(g.progress.unlocked(0))
        self.assertFalse(g.start(1))
        self.assertEqual(g.state,'MENU')
        self.assertFalse(g.progress.unlocked(2))

    def test_C_blocked_B_unlocks_and_next_resets(self):
        g=self.game();g.start();self.clear(g,25.001)
        self.assertEqual(g.grade,'C');g.next_level()
        self.assertEqual(g.level_index,0)
        self.assertFalse(g.start(1))
        g.restart();self.clear(g,25);g.next_level()
        self.assertEqual((g.level_index,g.elapsed),(1,0))
        self.assertFalse(g.progress.unlocked(2))
        self.clear(g,15);self.assertTrue(g.progress.unlocked(2))

    def test_replay_keeps_best_and_unlock(self):
        g=self.game();g.start();self.clear(g,20)
        g.restart();self.clear(g,30)
        self.assertEqual(g.progress.best[0],20)
        self.assertTrue(g.progress.unlocked(1))
        g.next_level();self.assertEqual(g.level_index,0) # 本次 C 不显示下一关
        g.menu();self.assertTrue(g.start(1)) # 之前已经解锁，可首页选择
        g.start(0);self.clear(g,12)
        self.assertEqual(g.progress.best[0],12)
        g.restart();g.update(36)
        self.assertEqual(g.progress.best[0],12)

    def test_roundtrip_persists_best(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'progress.json'
            g=self.game(Progress(3,path));g.start();self.clear(g,20)
            loaded=Progress(3,path)
            self.assertEqual(loaded.best,[20,None,None])
            self.assertTrue(loaded.unlocked(1))
            self.assertFalse(loaded.unlocked(2))

    def test_corrupt_save_safe_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'progress.json'
            for content in ['{bad', '[]', json.dumps({'version':1,'best_times':[None,10,None]}),
                            json.dumps({'version':1,'best_times':[True,None,None]}),
                            json.dumps({'version':1,'best_times':[float('nan'),None,None]})]:
                path.write_text(content)
                p=Progress(3,path)
                self.assertEqual(p.best,[None]*3)
                self.assertTrue(p.message)

    def test_save_failure_retains_in_memory_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Progress(3,Path(directory)/'progress.json')
            with patch.object(Path,'write_text',side_effect=OSError('read only')):
                p.record(0,15)
            self.assertTrue(p.unlocked(1))
            self.assertTrue(p.message)

    def test_locked_record_cannot_unlock_chain(self):
        p=Progress(3);p.record(1,10)
        self.assertEqual(p.best,[None]*3)
        self.assertFalse(p.unlocked(-1))
        self.assertFalse(p.unlocked(3))
