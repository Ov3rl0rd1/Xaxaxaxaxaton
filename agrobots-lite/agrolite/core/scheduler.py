from __future__ import annotations

import heapq
from typing import List, Optional, Tuple

from agrolite.core.algorithms import merge_sort, nearest
from agrolite.core.pathfinding import a_star
from agrolite.models.field import Field
from agrolite.models.robot import Robot
from agrolite.models.task import Task, TaskStatus


class Dispatcher:
    def __init__(self, field: Field) -> None:
        self.field = field
        self._heap: List[Task] = []
        self.failed: List[Task] = []

    def add(self, task: Task) -> None:
        task.status = TaskStatus.PENDING
        heapq.heappush(self._heap, task)

    @property
    def pending(self) -> List[Task]:
        return list(self._heap)

    def __len__(self) -> int:
        return len(self._heap)

    def day_plan(self) -> List[Task]:
        return merge_sort(self._heap, key=lambda t: t.sort_key())

    def expire(self, current_day: int) -> List[Task]:
        keep: List[Task] = []
        expired: List[Task] = []
        for task in self._heap:
            if task.deadline < current_day:
                task.status = TaskStatus.FAILED
                expired.append(task)
                self.failed.append(task)
            else:
                keep.append(task)
        heapq.heapify(keep)
        self._heap = keep
        return expired

    def assign_next(self, robots: List[Robot]) -> Optional[Tuple[Robot, Task]]:
        free = [r for r in robots if r.is_free and not r.needs_charge()]
        if not free:
            return None

        for task in sorted(self._heap):
            candidates = [r for r in free if r.can_handle(task)]
            if not candidates:
                continue
            robot = nearest(
                candidates,
                distance=lambda r: Field.manhattan(r.position, task.target),
            )
            if robot is None:
                continue
            path = a_star(self.field, robot.position, task.target)
            if path is None:
                continue
            self._heap.remove(task)
            heapq.heapify(self._heap)
            task.status = TaskStatus.ASSIGNED
            robot.assign(task, path)
            return robot, task
        return None
