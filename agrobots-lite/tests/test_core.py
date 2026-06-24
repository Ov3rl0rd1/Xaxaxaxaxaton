import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agrolite.core.algorithms import merge_sort, nearest
from agrolite.core.pathfinding import a_star
from agrolite.core.scheduler import Dispatcher
from agrolite.models.field import Field
from agrolite.models.robot import Harvester, Scout, Seeder
from agrolite.models.task import Task, TaskKind


def _grid():
    field = Field(5, 5)
    field.add_obstacle(2, 0)
    field.add_obstacle(2, 1)
    field.add_obstacle(2, 2)
    return field


def test_merge_sort_stable():
    data = [(3, "a"), (1, "b"), (3, "c"), (1, "d"), (2, "e")]
    result = merge_sort(data, key=lambda p: p[0])
    assert [p[0] for p in result] == [1, 1, 2, 3, 3]
    assert [p[1] for p in result] == ["b", "d", "e", "a", "c"]


def test_nearest():
    items = [3, -1, 7, 2]
    assert nearest(items, distance=lambda v: abs(v)) == -1
    assert nearest([], distance=lambda v: v) is None


def test_astar_finds_path_and_avoids_obstacles():
    field = _grid()
    path = a_star(field, (0, 0), (4, 0))
    assert path is not None
    assert (2, 0) not in path
    assert path[-1] == (4, 0)


def test_astar_unreachable():
    field = Field(3, 1)
    field.add_obstacle(1, 0)
    assert a_star(field, (0, 0), (2, 0)) is None


def test_robot_specialization():
    seeder = Seeder("s", 0, 0)
    harvester = Harvester("h", 0, 0)
    scout = Scout("e", 0, 0)
    assert seeder.can_handle(Task(TaskKind.SEED, 1, 1))
    assert not seeder.can_handle(Task(TaskKind.HARVEST, 1, 1))
    assert harvester.can_handle(Task(TaskKind.HARVEST, 1, 1))
    assert scout.can_handle(Task(TaskKind.INSPECT, 1, 1))
    assert scout.speed == 2


def test_dispatcher_priority_order():
    field = Field(5, 5)
    disp = Dispatcher(field)
    disp.add(Task(TaskKind.SEED, 1, 1, priority=3, deadline=5))
    disp.add(Task(TaskKind.SEED, 2, 2, priority=1, deadline=5))
    disp.add(Task(TaskKind.SEED, 3, 3, priority=2, deadline=5))
    plan = disp.day_plan()
    assert [t.priority for t in plan] == [1, 2, 3]


def test_simulation_runs_and_charges():
    from agrolite.scenarios import build_default_sim

    sim = build_default_sim()
    sim.run_days(3)
    assert sim.day == 4
    assert sim.stats.tasks_done >= 1


def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for test in tests:
        try:
            test()
            print(f"  OK   {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL {test.__name__}: {exc}")
    print(f"\n{passed}/{len(tests)} тестов пройдено.")
    return passed == len(tests)


if __name__ == "__main__":
    raise SystemExit(0 if _run_all() else 1)
