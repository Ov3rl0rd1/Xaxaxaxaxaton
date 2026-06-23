from __future__ import annotations

from typing import Dict, List, Tuple


class ServiceDepot:
    def __init__(self, parts: Dict[str, int] | None = None) -> None:
        self.parts: Dict[str, int] = dict(parts or {})
        self.repairs_done: int = 0

    def has_part(self, name: str, qty: int = 1) -> bool:
        return self.parts.get(name, 0) >= qty

    def take_part(self, name: str, qty: int = 1) -> bool:
        if not self.has_part(name, qty):
            return False
        self.parts[name] -= qty
        return True

    def restock(self, name: str, qty: int) -> None:
        self.parts[name] = self.parts.get(name, 0) + qty

    def catalog(self) -> List[Tuple[str, int]]:
        return sorted(self.parts.items(), key=lambda kv: kv[0])

    def low_stock(self, threshold: int = 2) -> List[str]:
        return [name for name, qty in self.parts.items() if qty <= threshold]
