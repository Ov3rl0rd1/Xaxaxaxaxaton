from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from agrobots.models.robot import Robot, RobotStatus
from agrobots.models.task import Task, TaskKind

WEATHER = {
    "ясно": 1.0,
    "облачно": 1.1,
    "дождь": 1.3,
    "жара": 1.25,
}


@dataclass
class EventResult:
    weather: str
    messages: List[str]
    new_tasks: List[Task]


class EventEngine:
    def __init__(self, field_w: int, field_h: int, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)
        self.field_w = field_w
        self.field_h = field_h
        self.weather = "ясно"

    def battery_factor(self) -> float:
        return WEATHER.get(self.weather, 1.0)

    def roll_day(self, robots: List[Robot], passable_cells: List) -> EventResult:
        messages: List[str] = []
        self.weather = self.rng.choice(list(WEATHER))
        messages.append(
            f"Погода: {self.weather} (расход батареи ×{self.battery_factor():.2f})"
        )

        new_tasks: List[Task] = []
        if passable_cells and self.rng.random() < 0.5:
            x, y = self.rng.choice(passable_cells)
            urgent = Task(TaskKind.INSPECT, x, y, priority=1, deadline=999, duration=1)
            new_tasks.append(urgent)
            messages.append(f"Срочный осмотр участка ({x},{y}) — задача #{urgent.id}")
        return EventResult(self.weather, messages, new_tasks)

    def maybe_breakdown(self, robot: Robot) -> Optional[str]:
        if robot.status in (RobotStatus.BROKEN, RobotStatus.SERVICE):
            return None
        chance = 0.01 + (robot.wear / 100.0) * 0.12
        if self.rng.random() < chance:
            return "перегрев привода" if robot.wear > 50 else "сбой датчика"
        return None
