from __future__ import annotations

import heapq
from collections import deque
from typing import Dict, List, Optional, Tuple

from agrobots.models.field import Field

Coord = Tuple[int, int]


def _reconstruct(came_from: Dict[Coord, Coord], start: Coord, goal: Coord) -> List[Coord]:
    path: List[Coord] = []
    node = goal
    while node != start:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path


def a_star(field: Field, start: Coord, goal: Coord) -> Optional[List[Coord]]:
    if start == goal:
        return []
    if not field.passable(*goal):
        return None

    open_heap: List[Tuple[int, int, Coord]] = []
    counter = 0
    heapq.heappush(open_heap, (Field.manhattan(start, goal), counter, start))
    came_from: Dict[Coord, Coord] = {}
    g_score: Dict[Coord, int] = {start: 0}

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            return _reconstruct(came_from, start, goal)
        for nb in field.neighbors(*current):
            tentative = g_score[current] + 1
            if tentative < g_score.get(nb, 1 << 30):
                came_from[nb] = current
                g_score[nb] = tentative
                f = tentative + Field.manhattan(nb, goal)
                counter += 1
                heapq.heappush(open_heap, (f, counter, nb))
    return None


def bfs(field: Field, start: Coord, goal: Coord) -> Optional[List[Coord]]:
    if start == goal:
        return []
    if not field.passable(*goal):
        return None

    frontier: deque[Coord] = deque([start])
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    while frontier:
        current = frontier.popleft()
        if current == goal:
            return _reconstruct(
                {k: v for k, v in came_from.items() if v is not None},
                start,
                goal,
            )
        for nb in field.neighbors(*current):
            if nb not in came_from:
                came_from[nb] = current
                frontier.append(nb)
    return None
