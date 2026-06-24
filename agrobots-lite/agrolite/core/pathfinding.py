from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

from agrolite.models.field import Field

Coord = Tuple[int, int]


def a_star(field: Field, start: Coord, goal: Coord) -> Optional[List[Coord]]:
    if not (field.passable(*start) and field.passable(*goal)):
        return None
    if start == goal:
        return []

    open_heap: List[Tuple[int, int, Coord]] = [(Field.manhattan(start, goal), 0, start)]
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    best_cost: Dict[Coord, int] = {start: 0}

    while open_heap:
        _f, g, current = heapq.heappop(open_heap)
        if current == goal:
            return _reconstruct(came_from, goal)
        for nxt in field.neighbors(*current):
            new_cost = g + 1
            if nxt not in best_cost or new_cost < best_cost[nxt]:
                best_cost[nxt] = new_cost
                came_from[nxt] = current
                priority = new_cost + Field.manhattan(nxt, goal)
                heapq.heappush(open_heap, (priority, new_cost, nxt))
    return None


def _reconstruct(came_from: Dict[Coord, Optional[Coord]], goal: Coord) -> List[Coord]:
    path: List[Coord] = []
    node: Optional[Coord] = goal
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path[1:]
