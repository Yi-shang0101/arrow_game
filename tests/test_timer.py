import unittest
from logic import Game, time_grade

class TimerTests(unittest.TestCase):
    def game(self):
        g=Game([{'board':[['U']]}]); g.start(); return g

    def test_grade_boundaries(self):
        for seconds, grade in [(0,'A'),(15,'A'),(15.000001,'B'),(25,'B'),
                               (25.000001,'C'),(35,'C'),(35.000001,None)]:
            with self.subTest(seconds=seconds): self.assertEqual(time_grade(seconds),grade)

    def test_timeout_idle_strictly_after_35(self):
        g=self.game(); g.update(35)
        self.assertEqual(g.state,'PLAYING')
        g.update(.001)
        self.assertEqual((g.state,g.failure_reason),('GAME_OVER','timeout'))
        frozen=g.elapsed; g.update(10)
        self.assertEqual(g.elapsed,frozen)
        self.assertEqual(g.click(0,0),'ignored')

    def test_finish_exact_boundary_even_slow_frame(self):
        for finish,grade in [(15,'A'),(25,'B'),(35,'C')]:
            g=self.game(); g.update(finish-.25); g.click(0,0); g.update(2)
            self.assertEqual((g.state,g.grade,g.elapsed),('ALL_CLEAR',grade,finish))
            g.update(20); self.assertEqual(g.elapsed,finish)

    def test_timeout_during_exit(self):
        g=self.game(); g.update(34.9); g.click(0,0); g.update(.3)
        self.assertEqual(g.failure_reason,'timeout')
        self.assertEqual(g.remaining,1)
        self.assertIsNone(g.animation)
        self.assertIsNone(g.grade)

    def test_restart_and_next_reset(self):
        g=Game([{'board':[['U']]},{'board':[['D']]}]); g.start()
        g.update(14); g.click(0,0); g.update(.25); g.next_level()
        self.assertEqual(g.elapsed,0)
        self.assertIsNone(g.grade)
        g.update(36); g.restart()
        self.assertEqual((g.elapsed,g.state,g.mistakes),(0,'PLAYING',3))
        self.assertIsNone(g.failure_reason)

    def test_menu_no_time_and_hint_does_not_pause(self):
        g=self.game(); g.show_hint(); g.update(5)
        self.assertEqual(g.elapsed,5)
        g.menu(); g.update(40); self.assertEqual(g.elapsed,5)
        g.start(); self.assertEqual(g.elapsed,0)

    def test_animation_and_idle_both_count(self):
        g=Game([{'board':[['R','U']]}]);g.start();g.update(10)
        g.click(0,0);g.update(.38)
        self.assertAlmostEqual(g.elapsed,10.38)
        self.assertEqual(g.mistakes,2)
        g.click(0,1);g.update(.25)
        self.assertAlmostEqual(g.elapsed,10.63)

    def test_third_level_animation_budget_allows_A(self):
        from levels import LEVELS
        from logic import solve, EXIT_DURATION
        g=Game(LEVELS);g.start(2)
        for r,c in solve(g.board):
            g.click(r,c);g.update(EXIT_DURATION)
        self.assertEqual(g.grade,'A')
        self.assertEqual(g.elapsed,7.5)
