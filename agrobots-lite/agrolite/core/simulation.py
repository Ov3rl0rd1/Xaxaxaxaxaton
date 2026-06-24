from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import List

from agrolite.core.pathfinding import a_star
from agrolite.core.scheduler import Dispatcher
from agrolite.models.field import Field
from agrolite.models.robot import Robot, RobotStatus
from agrolite.models.task import Task, TaskStatus


@dataclass
class Stats:
    tasks_done: int = 0
    tasks_failed: int = 0
    distance: int = 0
    energy_charged: float = 0.0


@dataclass
class Simulation:
    field: Field
    ticks_per_day: int = 8

    robots: List[Robot] = dc_field(default_factory=list)
    dispatcher: Dispatcher = dc_field(init=False)
    stats: Stats = dc_field(default_factory=Stats)
    log: List[str] = dc_field(default_factory=list)
    day: int = 1
    tick: int = 0

    def __post_init__(self) -> None:
        self.dispatcher = Dispatcher(self.field)

    def add_robot(self, robot: Robot) -> None:
        self.robots.append(robot)
        self._note(f"В парк добавлен {robot.kind_name} «{robot.name}» (#{robot.id})")

    def add_task(self, task: Task) -> None:
        self.dispatcher.add(task)
        self._note(f"Создан наряд {task.short()}")

    def step(self) -> None:
        if self.tick == 0:
            self._start_of_day()

        while self.dispatcher.assign_next(self.robots) is not None:
            pass

        for robot in self.robots:
            self._act(robot)

        self.tick += 1
        if self.tick >= self.ticks_per_day:
            self.tick = 0
            self.day += 1

    def run_day(self) -> None:
        start_day = self.day
        while self.day == start_day:
            self.step()

    def run_days(self, n: int) -> None:
        for _ in range(n):
            self.run_day()

    def _start_of_day(self) -> None:
        self._note(f"=== ДЕНЬ {self.day} ===")
        for t in self.dispatcher.expire(self.day):
            self.stats.tasks_failed += 1
            self._note(f"Задача #{t.id} просрочена и снята с выполнения")

    def _act(self, robot: Robot) -> None:
        if robot.task is not None:
            robot.errand = None
        elif robot.needs_charge() and not robot.path:
            if robot.position in self.field.charge_stations:
                robot.errand = "charge"
            else:
                self._send_to_charge(robot)

        if robot.path:
            self._move(robot)
            return

        if robot.errand == "charge" and robot.position in self.field.charge_stations:
            self._do_charge(robot)
            return

        if robot.task is not None:
            self._do_work(robot)
            return

        if robot.status is not RobotStatus.CHARGING:
            robot.status = RobotStatus.IDLE

    def _move(self, robot: Robot) -> None:
        robot.status = RobotStatus.MOVING
        before = robot.distance
        robot.step_move()
        self.stats.distance += robot.distance - before

    def _do_work(self, robot: Robot) -> None:
        task = robot.task
        assert task is not None
        robot.status = RobotStatus.WORKING
        task.status = TaskStatus.IN_PROGRESS
        robot._work_left -= 1
        robot.battery = max(0.0, robot.battery - robot.work_cost())
        if robot._work_left <= 0:
            self._complete_task(robot, task)

    def _complete_task(self, robot: Robot, task: Task) -> None:
        task.status = TaskStatus.DONE
        robot.task = None
        robot.done_tasks += 1
        robot.status = RobotStatus.IDLE
        self.stats.tasks_done += 1
        robot.record(f"задача #{task.id} ({task.kind.value}) выполнена")
        self._note(
            f"{robot.name}: ВЫПОЛНЕНА задача #{task.id} ({task.kind.value}) @{task.target}"
        )

    def _send_to_charge(self, robot: Robot) -> None:
        station = self.field.nearest_charge(*robot.position)
        if station is None:
            return
        path = a_star(self.field, robot.position, station)
        if path is not None:
            robot.errand = "charge"
            robot.set_route(path)
            robot.record(f"низкий заряд — маршрут на станцию {station}")
            self._note(f"{robot.name}: едет на зарядку ({robot.battery:.0f}%)")

    def _do_charge(self, robot: Robot) -> None:
        before = robot.battery
        robot.charge_tick()
        self.stats.energy_charged += robot.battery - before
        if robot.battery >= robot.max_battery:
            robot.errand = None

    def _note(self, message: str) -> None:
        self.log.append(f"[Д{self.day} Т{self.tick}] {message}")

    def recent_log(self, n: int = 60) -> List[str]:
        return self.log[-n:]
