"""最佳成绩存档：只保存成功通关的最短时间，由成绩推导解锁状态。"""
import json
import math
from pathlib import Path


class Progress:
    def __init__(self, count, path=None):
        self.best = [None] * count
        self.path = Path(path) if path is not None else None
        self.message = ''
        if self.path and self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding='utf-8'))
                if not isinstance(data, dict) or data.get('version') != 1:
                    raise ValueError('存档格式无效')
                values = data.get('best_times')
                if not isinstance(values, list) or len(values) != count:
                    raise ValueError('关卡数量不匹配')
                for i, value in enumerate(values):
                    if value is not None and (type(value) not in (int, float) or
                            not math.isfinite(value) or not 0 <= value <= 35):
                        raise ValueError('成绩无效')
                    # 不能用不完整的前置成绩解锁后续关卡。
                    if value is not None and not all(v is not None and v <= 25 for v in values[:i]):
                        raise ValueError('前置关卡未达标')
                self.best = values[:]
            except (OSError, ValueError, TypeError):
                self.message = '存档未能读取，本次从第一关开始。'

    def unlocked(self, index):
        return (0 <= index < len(self.best) and
                all(v is not None and v <= 25 for v in self.best[:index]))

    def record(self, index, seconds):
        if not self.unlocked(index) or not math.isfinite(seconds) or not 0 <= seconds <= 35:
            return
        previous = self.best[index]
        if previous is None or seconds < previous:
            self.best[index] = seconds
            self.save()

    def save(self):
        if self.path is None:
            return
        temporary = self.path.with_suffix('.tmp')
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps({'version': 1, 'best_times': self.best},
                                           ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(self.path)
            self.message = ''
        except OSError:
            self.message = '成绩暂未保存，关闭游戏后可能丢失。'
