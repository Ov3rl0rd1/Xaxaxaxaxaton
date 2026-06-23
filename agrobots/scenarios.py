from __future__ import annotations

from agrobots.core.simulation import Simulation
from agrobots.models.field import Field
from agrobots.models.robot import Harvester, Scout, Seeder
from agrobots.models.task import Task, TaskKind
from agrobots.models.warehouse import ServiceDepot


def build_default_field() -> Field:
    field = Field(14, 9)
    field.set_depot(0, 0)
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


def build_default_depot() -> ServiceDepot:
    return ServiceDepot(
        {
            "gearbox": 4,
            "seeds": 12,
            "water_filter": 6,
            "battery_cell": 3,
            "tire": 5,
        }
    )


def build_default_sim(seed: int = 42) -> Simulation:
    field = build_default_field()
    depot = build_default_depot()
    sim = Simulation(field=field, depot=depot, ticks_per_day=8, seed=seed)

    sim.add_robot(Seeder("Сеятель-1", 0, 0))
    sim.add_robot(Seeder("Сеятель-2", 1, 0))
    sim.add_robot(Harvester("Жнец-1", 0, 1))
    sim.add_robot(Scout("Дрон-1", 1, 1))

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
