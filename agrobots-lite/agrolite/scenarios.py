from __future__ import annotations

from agrolite.core.simulation import Simulation
from agrolite.models.field import Field
from agrolite.models.robot import Harvester, Scout, Seeder
from agrolite.models.task import Task, TaskKind


def build_default_field() -> Field:
    field = Field(14, 9)
    field.add_charge_station(0, 0)
    field.add_charge_station(13, 0)
    field.add_charge_station(0, 8)

    obstacles = [
        (4, 1), (4, 2), (4, 3),
        (7, 5), (8, 5), (9, 5),
        (10, 2), (10, 3),
        (2, 6), (3, 6),
        (11, 7),
    ]
    for x, y in obstacles:
        field.add_obstacle(x, y)
    return field


def build_default_sim() -> Simulation:
    field = build_default_field()
    sim = Simulation(field=field, ticks_per_day=8)

    sim.add_robot(Seeder("Сеятель-1", 1, 0))
    sim.add_robot(Seeder("Сеятель-2", 1, 1))
    sim.add_robot(Harvester("Жнец-1", 0, 1))
    sim.add_robot(Scout("Дрон-1", 2, 1))

    starter = [
        Task(TaskKind.SEED, 6, 2, priority=2, deadline=2, duration=2),
        Task(TaskKind.SEED, 12, 6, priority=3, deadline=3, duration=2),
        Task(TaskKind.IRRIGATE, 5, 7, priority=2, deadline=2, duration=2),
        Task(TaskKind.HARVEST, 13, 8, priority=1, deadline=2, duration=3),
        Task(TaskKind.HARVEST, 9, 1, priority=3, deadline=4, duration=3),
        Task(TaskKind.INSPECT, 2, 4, priority=4, deadline=3, duration=1),
        Task(TaskKind.INSPECT, 11, 4, priority=2, deadline=2, duration=1),
        Task(TaskKind.SEED, 3, 8, priority=3, deadline=4, duration=2),
    ]
    for t in starter:
        sim.add_task(t)
    return sim
