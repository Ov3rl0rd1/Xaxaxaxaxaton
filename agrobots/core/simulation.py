from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import List, Optional

from agrobots.core.events import EventEngine
from agrobots.core.pathfinding import a_star
from agrobots.core.scheduler import Dispatcher
from agrobots.models.field import CellKind, Field
from agrobots.models.robot import Robot, RobotStatus
from agrobots.models.task import Task, TaskStatus
from agrobots.models.warehouse import ServiceDepot

REPAIR_PART = "gearbox"
REPAIR_TICKS = 2


@dataclass
class Stats:
    tasks_done: int = 0
    tasks_failed: int = 0
    distance: int = 0
    breakdowns: int = 0
    repairs: int = 0
    energy_charged: float = 0.0


@dataclass
class Simulation:
    field: Field
    depot: ServiceDepot
    ticks_per_day: int = 8
    seed: Optional[int] = 42

    robots: List[Robot] = dc_field(default_factory=list)
    dispatcher: Dispatcher = dc_field(init=False)
    events: EventEngine = dc_field(init=False)
    stats: Stats = dc_field(default_factory=Stats)
    log: List[str] = dc_field(default_factory=list)
    day: int = 1
    tick: int = 0

    def __post_init__(self) -> None:
        self.dispatcher = Dispatcher(self.field)
        self.events = EventEngine(self.field.width, self.field.height, self.seed)
        self._passable_cells = [
            (c.x, c.y)
            for row in self.field.grid
            for c in row
            if c.kind in (CellKind.FREE,)
        ]

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
        expired = self.dispatcher.expire(self.day)
        for t in expired:
            self.stats.tasks_failed += 1
            self._note(f"Задача #{t.id} просрочена и снята с выполнения")
        result = self.events.roll_day(self.robots, self._passable_cells)
        for msg in result.messages:
            self._note(msg)
        for task in result.new_tasks:
            self.dispatcher.add(task)

    def _act(self, robot: Robot) -> None:
        if robot.status is RobotStatus.BROKEN:
            self._handle_broken(robot)
            return
        if robot.status is RobotStatus.SERVICE:
            robot.repair_left -= 1
            if robot.repair_left <= 0:
                robot.repair()
                robot.battery = max(robot.battery, 50.0)
                self.stats.repairs += 1
                self._note(f"{robot.name}: ремонт завершён, робот снова в строю")
            return

        if robot.errand is None and robot.task is None and robot.needs_charge():
            self._send_to_charge(robot)
        elif robot.errand is None and robot.task is None and robot.needs_service():
            self._send_to_depot(robot)

        if robot.path:
            self._move(robot)
            return

        if robot.errand == "charge" and robot.position in self.field.charge_stations:
            self._do_charge(robot)
            return
        if robot.errand == "service" and robot.position == self.field.depot:
            self._begin_service(robot)
            return
        if robot.task is not None:
            self._do_work(robot)
            return

        if robot.status is not RobotStatus.CHARGING:
            robot.status = RobotStatus.IDLE

    def _move(self, robot: Robot) -> None:
        robot.status = RobotStatus.MOVING
        before = robot.battery
        still_moving = robot.step_move()
        extra = (before - robot.battery) * (self.events.battery_factor() - 1.0)
        robot.battery = max(0.0, robot.battery - extra)
        self.stats.distance += robot.speed if still_moving else 0

        if robot.battery <= 0:
            self._trigger_breakdown(robot, reason="полный разряд аккумулятора")
            return
        reason = self.events.maybe_breakdown(robot)
        if reason:
            self._trigger_breakdown(robot, reason)

    def _do_work(self, robot: Robot) -> None:
        task = robot.task
        assert task is not None
        robot.status = RobotStatus.WORKING
        task.status = TaskStatus.IN_PROGRESS
        robot._work_left -= 1
        robot.battery = max(0.0, robot.battery - robot.work_cost())
        robot.wear = min(100.0, robot.wear + 1.2)

        if robot.battery <= 0:
            self._trigger_breakdown(robot, reason="разряд во время работы")
            return

        if robot._work_left <= 0:
            self._complete_task(robot, task)

    def _complete_task(self, robot: Robot, task: Task) -> None:
        if task.required_part:
            if self.depot.take_part(task.required_part, 1):
                robot.record(f"израсходован расходник '{task.required_part}'")
            else:
                self._note(
                    f"ВНИМАНИЕ: на складе нет '{task.required_part}' для задачи #{task.id}"
                )
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

    def _send_to_depot(self, robot: Robot) -> None:
        if self.field.depot is None:
            return
        path = a_star(self.field, robot.position, self.field.depot)
        if path is not None:
            robot.errand = "service"
            robot.set_route(path)
            robot.record(f"высокий износ ({robot.wear:.0f}%) — маршрут в сервис")
            self._note(f"{robot.name}: едет на ТО (износ {robot.wear:.0f}%)")

    def _begin_service(self, robot: Robot) -> None:
        if self.depot.take_part(REPAIR_PART, 1):
            robot.status = RobotStatus.SERVICE
            robot.repair_left = REPAIR_TICKS
            robot.errand = None
            self.depot.repairs_done += 1
            self._note(f"{robot.name}: начато ТО (списан '{REPAIR_PART}')")
        else:
            robot.errand = None
            robot.status = RobotStatus.IDLE
            self._note(f"ВНИМАНИЕ: нет детали '{REPAIR_PART}' для ТО {robot.name}")

    def _trigger_breakdown(self, robot: Robot, reason: str) -> None:
        failed_task = robot.break_down(reason)
        robot.errand = None
        self.stats.breakdowns += 1
        self._note(f"{robot.name}: ПОЛОМКА — {reason}")
        if failed_task is not None:
            failed_task.status = TaskStatus.PENDING
            self.dispatcher.add(failed_task)

    def _handle_broken(self, robot: Robot) -> None:
        if self.depot.take_part(REPAIR_PART, 1):
            robot.status = RobotStatus.SERVICE
            robot.repair_left = REPAIR_TICKS
            self.depot.repairs_done += 1
            self._note(
                f"{robot.name}: к месту поломки выехал сервис (списан '{REPAIR_PART}')"
            )

    def _note(self, message: str) -> None:
        self.log.append(f"[Д{self.day} Т{self.tick}] {message}")

    def recent_log(self, n: int = 12) -> List[str]:
        return self.log[-n:]
