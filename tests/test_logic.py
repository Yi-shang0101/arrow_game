import unittest
from levels import LEVELS
from logic import Game, DIRECTIONS, can_exit, solve, available_moves, validate_board

class RuleTests(unittest.TestCase):
    def test_four_directions_distant_blockers(self):
        for direction,(dr,dc) in DIRECTIONS.items():
            with self.subTest(direction=direction):
                board=[[None]*5 for _ in range(5)]
                board[2][2]=direction
                self.assertTrue(can_exit(board,2,2))
                board[2+2*dr][2+2*dc]='R'
                self.assertFalse(can_exit(board,2,2))
                board[2+2*dr][2+2*dc]=None
                board[2-dr][2-dc]='D'  # 后方箭头不阻挡
                self.assertTrue(can_exit(board,2,2))

    def test_T03_all_boundaries(self):
        for d,r,c in [('U',0,1),('D',2,1),('L',1,0),('R',1,2)]:
            b=[[None]*3 for _ in range(3)]
            b[r][c]=d
            self.assertTrue(can_exit(b,r,c))

    def test_invalid_and_empty(self):
        b=[[None,'R']]
        for r,c in [(0,0),(-1,1),(0,-1),(1,0),(0,2)]:
            self.assertFalse(can_exit(b,r,c))
        for bad in [[],[[]],[['U'],['L','R']],[['X']]]:
            with self.assertRaises(ValueError): validate_board(bad)

    def test_deadlock(self):
        self.assertIsNone(solve([['R','L']]))

    def test_all_levels_solvable_and_four_directions(self):
        for level in LEVELS:
            board=level['board']
            before=[r[:] for r in board]
            solution=solve(board)
            self.assertIsNotNone(solution)
            self.assertEqual(len(solution),sum(v is not None for row in board for v in row))
            self.assertEqual({v for row in board for v in row if v},set(DIRECTIONS))
            self.assertEqual(before,board)
            for r,c in solution:
                self.assertTrue(can_exit(before,r,c))
                before[r][c]=None

class FlowTests(unittest.TestCase):
    def setUp(self):
        self.g=Game([{'board':[['R','U']]},{'board':[['D']]}])
        self.g.start()

    def test_T01_exit_commit_after_animation(self):
        self.assertEqual(self.g.click(0,1),'exit')
        self.assertEqual(self.g.remaining,2)
        self.g.update(.2)
        self.assertEqual(self.g.remaining,2)
        self.g.update(.4)
        self.assertIsNone(self.g.board[0][1])
        self.assertEqual(self.g.mistakes,3)

    def test_T02_collision_and_click_lock(self):
        self.assertEqual(self.g.click(0,0),'bump')
        for _ in range(10): self.assertEqual(self.g.click(0,0),'ignored')
        self.assertEqual(self.g.mistakes,2)
        self.g.update(.4)
        self.assertEqual(self.g.board,[['R','U']])

    def test_T04_next_and_all_clear(self):
        for r,c in [(0,1),(0,0)]:
            self.g.click(r,c)
            self.g.update(1)
        self.assertEqual(self.g.state,'LEVEL_CLEAR')
        self.g.next_level()
        self.assertEqual(self.g.level_index,1)
        self.assertEqual(self.g.mistakes,3)
        self.g.click(0,0)
        self.g.update(1)
        self.assertEqual(self.g.state,'ALL_CLEAR')
        self.assertEqual(self.g.click(0,0),'ignored')

    def test_T05_failure_restart(self):
        for _ in range(3):
            self.g.click(0,0)
            self.g.update(1)
        self.assertEqual(self.g.state,'GAME_OVER')
        self.assertEqual(self.g.mistakes,0)
        self.assertEqual(self.g.click(0,1),'ignored')
        self.g.restart()
        self.assertEqual(self.g.state,'PLAYING')
        self.assertEqual(self.g.mistakes,3)

    def test_T06_restart_during_animation(self):
        self.g.click(0,1)
        self.g.update(1)
        self.g.click(0,0)
        self.g.restart()
        self.g.update(2)
        self.assertEqual(self.g.board,[['R','U']])
        self.assertEqual(self.g.levels[0]['board'],[['R','U']])
        self.assertIsNone(self.g.animation)

    def test_hint_empty_outside_menu(self):
        self.g.show_hint()
        self.assertEqual(self.g.hint,(0,1))
        self.assertEqual(self.g.mistakes,3)
        self.g.update(2.1)
        self.assertIsNone(self.g.hint)
        for r,c in [(-1,0),(0,2),(1,0)]: self.assertEqual(self.g.click(r,c),'ignored')
        self.g.click(0,1)
        self.g.update(1)
        self.assertEqual(self.g.click(0,1),'ignored')
        self.g.click(0,0)
        self.g.menu()
        self.g.update(2)
        self.assertEqual(self.g.state,'MENU')
        self.assertIsNone(self.g.animation)

if __name__=='__main__': unittest.main()
