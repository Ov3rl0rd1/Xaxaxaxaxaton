from __future__ import annotations

import enum
import itertools
from typing import Tuple

Coord = Tuple[int, int]


class TaskKind(enum.Enum):
    SEED = "посев"
    HARVEST = "сбор"
    INSPECT = "осмотр"
    IRRIGATE = "полив"


class TaskStatus(enum.Enum):
    PENDING = "ожидает"
    ASSIGNED = "назначена"
    IN_PROGRESS = "выполняется"
    DONE = "выполнена"
    FAILED = "просрочена"


class Task:
    _ids = itertools.count(1)

    def __init__(
        self,
        kind: TaskKind,
        x: int,
        y: int,
        priority: int = 3,
        deadline: int = 5,
        duration: int = 2,
    ) -> None:
        self.id: int = next(self._ids)
        self.kind = kind
        self.x = x
        self.y = y
        self.priority = priority
        self.deadline = deadline
        self.duration = duration
        self.status = TaskStatus.PENDING
        self._seq = self.id

    @property
    def target(self) -> Coord:
        return (self.x, self.y)

    def sort_key(self) -> Tuple[int, int, int]:
        return (self.priority, self.deadline, self._seq)

    def __lt__(self, other: "Task") -> bool:
        return self.sort_key() < other.sort_key()

    def __repr__(self) -> str:
        return (
            f"Task#{self.id}({self.kind.name} @{self.target} "
            f"p{self.priority} d{self.deadline} {self.status.name})"
        )

    def short(self) -> str:
        return (
            f"#{self.id:<2} {self.kind.value:<7} ({self.x},{self.y}) "
            f"P{self.priority} срок:день{self.deadline} [{self.status.value}]"
        )
