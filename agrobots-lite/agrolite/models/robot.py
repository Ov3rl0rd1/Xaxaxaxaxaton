from __future__ import annotations

import enum
import itertools
from collections import deque
from typing import Deque, List, Optional, Tuple

from agrolite.models.task import Task, TaskKind

Coord = Tuple[int, int]


class RobotStatus(enum.Enum):
    IDLE = "простой"
    MOVING = "в пути"
    WORKING = "работает"
    CHARGING = "зарядка"


class Robot:
    _ids = itertools.count(1)
    HANDLES: frozenset[TaskKind] = frozenset(TaskKind)
    ICON = "R"

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        battery: float = 100.0,
        speed: int = 1,
    ) -> None:
        self.id: int = next(Robot._ids)
        self.name = name
        self.x = x
        self.y = y
        self.home: Coord = (x, y)
        self.max_battery = 100.0
        self.battery = float(battery)
        self.speed = max(1, speed)
        self.status = RobotStatus.IDLE

        self.path: Deque[Coord] = deque()
        self.task: Optional[Task] = None
        self._work_left = 0
        self.errand: Optional[str] = None

        self.log: List[str] = []
        self.distance = 0
        self.done_tasks = 0

    @property
    def kind_name(self) -> str:
        return type(self).__name__

    def can_handle(self, task: Task) -> bool:
        return task.kind in self.HANDLES

    def move_cost(self) -> float:
        return 1.5

    def work_cost(self) -> float:
        return 3.0

    @property
    def position(self) -> Coord:
        return (self.x, self.y)

    @property
    def is_free(self) -> bool:
        return self.task is None and self.status in (
            RobotStatus.IDLE,
            RobotStatus.CHARGING,
        )

    def needs_charge(self) -> bool:
        return self.battery <= 25.0

    def assign(self, task: Task, path: list[Coord]) -> None:
        self.task = task
        self.path = deque(path)
        self._work_left = task.duration
        self.status = RobotStatus.MOVING
        self.record(f"назначена задача #{task.id} ({task.kind.value})")

    def set_route(self, path: list[Coord]) -> None:
        self.path = deque(path)
        if path:
            self.status = RobotStatus.MOVING

    def step_move(self) -> bool:
        for _ in range(self.speed):
            if not self.path:
                break
            self.x, self.y = self.path.popleft()
            self.distance += 1
            self.battery = max(0.0, self.battery - self.move_cost())
        return bool(self.path)

    def charge_tick(self, rate: float = 20.0) -> None:
        self.status = RobotStatus.CHARGING
        self.battery = min(self.max_battery, self.battery + rate)
        if self.battery >= self.max_battery:
            self.battery = self.max_battery
            self.status = RobotStatus.IDLE
            self.record("зарядка завершена (100%)")

    def record(self, message: str) -> None:
        self.log.append(message)

    def __repr__(self) -> str:
        return f"{self.kind_name}#{self.id}<{self.name}>"


class Seeder(Robot):
    HANDLES = frozenset({TaskKind.SEED, TaskKind.IRRIGATE})
    ICON = "S"

    def work_cost(self) -> float:
        return 2.5


class Harvester(Robot):
    HANDLES = frozenset({TaskKind.HARVEST})
    ICON = "H"

    def move_cost(self) -> float:
        return 2.2

    def work_cost(self) -> float:
        return 4.5


class Scout(Robot):
    HANDLES = frozenset({TaskKind.INSPECT})
    ICON = "E"

    def __init__(self, name: str, x: int, y: int, battery: float = 100.0) -> None:
        super().__init__(name, x, y, battery=battery, speed=2)

    def move_cost(self) -> float:
        return 0.9

    def work_cost(self) -> float:
        return 1.5


_FACTORY = {
    "seeder": Seeder,
    "harvester": Harvester,
    "scout": Scout,
}


def build_robot(kind: str, name: str, x: int, y: int) -> Robot:
    cls = _FACTORY.get(kind.lower())
    if cls is None:
        raise ValueError(
            f"Неизвестный тип робота '{kind}'. Доступно: {', '.join(_FACTORY)}"
        )
    return cls(name, x, y)
