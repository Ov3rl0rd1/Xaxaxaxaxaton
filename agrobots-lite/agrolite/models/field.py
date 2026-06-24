from __future__ import annotations

import enum
from typing import Iterator, List, Optional, Tuple

Coord = Tuple[int, int]


class CellKind(enum.Enum):
    FREE = "."
    OBSTACLE = "#"
    CHARGE = "C"


class Cell:
    __slots__ = ("x", "y", "kind")

    def __init__(self, x: int, y: int, kind: CellKind = CellKind.FREE) -> None:
        self.x = x
        self.y = y
        self.kind = kind

    @property
    def coord(self) -> Coord:
        return (self.x, self.y)

    @property
    def passable(self) -> bool:
        return self.kind is not CellKind.OBSTACLE

    def __repr__(self) -> str:
        return f"Cell({self.x},{self.y},{self.kind.name})"


class Field:
    def __init__(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Размер поля должен быть положительным")
        self.width = width
        self.height = height
        self.grid: List[List[Cell]] = [
            [Cell(x, y) for x in range(width)] for y in range(height)
        ]
        self.charge_stations: List[Coord] = []

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def cell(self, x: int, y: int) -> Cell:
        if not self.in_bounds(x, y):
            raise IndexError(f"Клетка ({x},{y}) вне поля")
        return self.grid[y][x]

    def passable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.grid[y][x].passable

    def neighbors(self, x: int, y: int) -> Iterator[Coord]:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if self.passable(nx, ny):
                yield (nx, ny)

    def set_kind(self, x: int, y: int, kind: CellKind) -> None:
        cell = self.cell(x, y)
        cell.kind = kind
        if kind is CellKind.CHARGE and cell.coord not in self.charge_stations:
            self.charge_stations.append(cell.coord)

    def add_obstacle(self, x: int, y: int) -> None:
        self.set_kind(x, y, CellKind.OBSTACLE)

    def add_charge_station(self, x: int, y: int) -> None:
        self.set_kind(x, y, CellKind.CHARGE)

    def nearest_charge(self, x: int, y: int) -> Optional[Coord]:
        if not self.charge_stations:
            return None
        return min(
            self.charge_stations,
            key=lambda c: abs(c[0] - x) + abs(c[1] - y),
        )

    @staticmethod
    def manhattan(a: Coord, b: Coord) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
