from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agrobots.core.algorithms import binary_search, merge_sort, nearest
from agrobots.core.pathfinding import a_star, bfs
from agrobots.core.scheduler import Dispatcher
from agrobots.models.field import Field
from agrobots.models.robot import Harvester, Scout, Seeder
from agrobots.models.task import Task, TaskKind
from agrobots.scenarios import build_default_sim
from agrobots.structures.linked_list import LinkedList


def test_linked_list_append_and_iter():
    ll: LinkedList[int] = LinkedList()
    for i in range(5):
        ll.append(i)
    assert len(ll) == 5
    assert list(ll) == [0, 1, 2, 3, 4]
    assert ll.last() == 4
    assert ll.tail(2) == [3, 4]


def test_merge_sort_stable():
    data = [(3, "a"), (1, "b"), (3, "c"), (2, "d"), (1, "e")]
    out = merge_sort(data, key=lambda p: p[0])
    assert [p[0] for p in out] == [1, 1, 2, 3, 3]
    assert out[0][1] == "b" and out[1][1] == "e"
    assert out[3][1] == "a" and out[4][1] == "c"


def test_binary_search():
    catalog = [("apple", 1), ("mango", 2), ("pear", 3), ("zebra", 4)]
    assert binary_search(catalog, "mango") == 2
    assert binary_search(catalog, "zebra") == 4
    assert binary_search(catalog, "missing") is None


def test_nearest():
    pts = [(0, 0), (5, 5), (1, 1)]
    best = nearest(pts, distance=lambda p: abs(p[0]) + abs(p[1]))
    assert best == (0, 0)


def test_astar_finds_path_and_avoids_obstacles():
    field = Field(5, 1)
    path = a_star(field, (0, 0), (4, 0))
    assert path == [(1, 0), (2, 0), (3, 0), (4, 0)]
    field2 = Field(3, 1)
    field2.add_obstacle(1, 0)
    assert a_star(field2, (0, 0), (2, 0)) is None


def test_astar_matches_bfs_length():
    field = Field(6, 6)
    field.add_obstacle(2, 2)
    field.add_obstacle(2, 3)
    a = a_star(field, (0, 0), (5, 5))
    b = bfs(field, (0, 0), (5, 5))
    assert a is not None and b is not None
    assert len(a) == len(b)


def test_robot_specialization():
    seeder = Seeder("s", 0, 0)
    harv = Harvester("h", 0, 0)
    scout = Scout("e", 0, 0)
    assert seeder.can_handle(Task(TaskKind.SEED, 1, 1))
    assert not seeder.can_handle(Task(TaskKind.HARVEST, 1, 1))
    assert harv.can_handle(Task(TaskKind.HARVEST, 1, 1))
    assert scout.speed == 2


def test_dispatcher_priority_order():
    field = Field(5, 5)
    disp = Dispatcher(field)
    disp.add(Task(TaskKind.SEED, 1, 1, priority=3))
    disp.add(Task(TaskKind.SEED, 2, 2, priority=1))
    disp.add(Task(TaskKind.SEED, 3, 3, priority=2))
    plan = disp.day_plan()
    assert [t.priority for t in plan] == [1, 2, 3]


def test_simulation_runs_and_completes_tasks():
    sim = build_default_sim(seed=42)
    sim.run_days(3)
    assert sim.stats.tasks_done > 0
    assert sim.day == 4


def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  OK   {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL {fn.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} тестов пройдено.")
    return failed


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
