"""不依赖图形库的游戏规则。坐标统一为 (row, col)。"""
from dataclasses import dataclass
from progress import Progress

TIME_LIMIT = 35.0
EXIT_DURATION = 0.25
BUMP_DURATION = 0.38

DIFFICULTY_RULES = {
    'normal': {'label': '普通', 'A': 15.0, 'B': 25.0, 'C': 35.0, 'time_limit': 35.0},
    'hard': {'label': '困难', 'A': 25.0, 'B': 40.0, 'C': 55.0, 'time_limit': 55.0},
    'expert': {'label': '专家', 'A': 35.0, 'B': 55.0, 'C': 75.0, 'time_limit': 75.0},
}


def level_rules(level):
    """根据关卡难度返回评级与限时规则；旧关卡默认使用普通难度。"""
    return DIFFICULTY_RULES.get(level.get('difficulty', 'normal'), DIFFICULTY_RULES['normal'])


def time_grade(seconds, rules=None):
    """按当前难度的耗时阈值评级；超过该难度限时无评级。"""
    rules = rules or DIFFICULTY_RULES['normal']
    if seconds <= rules['A']:
        return "A"
    if seconds <= rules['B']:
        return "B"
    if seconds <= rules['C']:
        return "C"
    return None


DIRECTIONS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


def validate_board(board):
    if not board or not board[0] or any(len(row) != len(board[0]) for row in board):
        raise ValueError("棋盘必须是非空矩形")
    if any(cell is not None and cell not in DIRECTIONS for row in board for cell in row):
        raise ValueError("箭头方向只能是 U/D/L/R，空格为 None")


def can_exit(board, row, col):
    """沿射线检查到边界；阻挡者的方向不影响判断。"""
    if not (0 <= row < len(board) and 0 <= col < len(board[0])):
        return False
    direction = board[row][col]
    if direction is None:
        return False
    dr, dc = DIRECTIONS[direction]
    r, c = row + dr, col + dc
    while 0 <= r < len(board) and 0 <= c < len(board[0]):
        if board[r][c] is not None:
            return False
        r, c = r + dr, c + dc
    return True


def available_moves(board):
    return [(r, c) for r, row in enumerate(board) for c, cell in enumerate(row)
            if cell is not None and can_exit(board, r, c)]


def solve(board):
    """返回一种解法；死锁返回 None。移除只会减少阻挡，无需回溯。"""
    validate_board(board)
    work = [row[:] for row in board]
    result = []
    while any(cell is not None for row in work for cell in row):
        moves = available_moves(work)
        if not moves:
            return None
        for r, c in moves:
            work[r][c] = None
            result.append((r, c))
    return result


@dataclass
class Animation:
    row: int
    col: int
    direction: str
    kind: str
    elapsed: float = 0.0


class Game:
    """逻辑状态和动画事务；飞出完成后才删除，动画期间不接受棋盘点击。"""
    def __init__(self, levels, mistakes=3, progress=None):
        self.levels = levels
        time_limits = [level_rules(level)['time_limit'] for level in levels]
        unlock_times = [level_rules(level)['B'] for level in levels]
        if progress is None:
            progress = Progress(len(levels), time_limits=time_limits,
                                unlock_times=unlock_times)
        else:
            progress.configure(time_limits=time_limits, unlock_times=unlock_times)
        self.progress = progress
        self.max_mistakes = mistakes
        self.level_index = 0
        self.state = "MENU"
        self.board = []
        self.animation = None
        self.mistakes = mistakes
        self.hint = None
        self.hint_time = 0.0
        self.used_hints = 0
        self.elapsed = 0.0
        self.grade = None
        self.failure_reason = None

    @property
    def remaining(self):
        return sum(cell is not None for row in self.board for cell in row)

    @property
    def level_rules(self):
        return level_rules(self.levels[self.level_index])

    @property
    def time_limit(self):
        return self.level_rules['time_limit']

    def start(self, index=0):
        if not 0 <= index < len(self.levels):
            raise ValueError("关卡索引越界")
        if not self.progress.unlocked(index):
            return False
        self.level_index = index
        initial = self.levels[index]["board"]
        validate_board(initial)
        self.board = [row[:] for row in initial]
        self.mistakes = self.max_mistakes
        self.animation = None
        self.hint = None
        self.hint_time = 0.0
        self.used_hints = 0
        self.elapsed = 0.0
        self.grade = None
        self.failure_reason = None
        self.state = "PLAYING"
        return True

    def restart(self):
        self.start(self.level_index)

    def menu(self):
        self.animation = None
        self.hint = None
        self.state = "MENU"

    def next_level(self):
        if self.state == "LEVEL_CLEAR" and self.grade in ("A", "B"):
            self.start(self.level_index + 1)

    def click(self, row, col):
        if self.state != "PLAYING" or self.animation:
            return "ignored"
        if not (0 <= row < len(self.board) and 0 <= col < len(self.board[0])):
            return "ignored"
        direction = self.board[row][col]
        if direction is None:
            return "ignored"
        self.hint = None
        kind = "exit" if can_exit(self.board, row, col) else "bump"
        if kind == "bump":
            self.mistakes -= 1
        self.animation = Animation(row, col, direction, kind)
        return kind

    def show_hint(self):
        if self.state != "PLAYING" or self.animation:
            return
        moves = available_moves(self.board)
        if moves:
            self.hint = moves[0]
            self.hint_time = 2.0
            self.used_hints += 1

    def update(self, dt):
        if dt < 0:
            raise ValueError("时间间隔不能为负数")
        if self.state != "PLAYING":
            return
        # 最后一支箭头可能在本帧结束之前飞完，按实际完成时刻结算。
        animation = self.animation
        duration = EXIT_DURATION if animation and animation.kind == "exit" else BUMP_DURATION
        terminal = animation and ((animation.kind == "exit" and self.remaining == 1)
                                  or (animation.kind == "bump" and self.mistakes == 0))
        advance = min(dt, max(0.0, duration-animation.elapsed)) if terminal else dt
        self.elapsed = round(self.elapsed + advance, 9)
        if self.elapsed > self.time_limit:
            self.state = "GAME_OVER"
            self.failure_reason = "timeout"
            self.animation = None
            self.hint = None
            return
        self.hint_time = max(0.0, self.hint_time - advance)
        if self.hint_time == 0:
            self.hint = None
        if not animation:
            return
        animation.elapsed = round(animation.elapsed + advance, 9)
        if animation.elapsed < duration:
            return
        self.animation = None
        if animation.kind == "exit":
            self.board[animation.row][animation.col] = None
            if self.remaining == 0:
                self.grade = time_grade(self.elapsed, self.level_rules)
                self.progress.record(self.level_index, self.elapsed, self.time_limit)
                self.state = "ALL_CLEAR" if self.level_index == len(self.levels)-1 else "LEVEL_CLEAR"
        elif self.mistakes == 0:
            self.failure_reason = "mistakes"
            self.state = "GAME_OVER"
