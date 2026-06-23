from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")
K = TypeVar("K")


def merge_sort(items: Sequence[T], key: Callable[[T], object]) -> List[T]:
    data = list(items)
    if len(data) <= 1:
        return data
    mid = len(data) // 2
    left = merge_sort(data[:mid], key)
    right = merge_sort(data[mid:], key)
    return _merge(left, right, key)


def _merge(left: List[T], right: List[T], key: Callable[[T], object]) -> List[T]:
    result: List[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def binary_search(catalog: Sequence[Tuple[str, T]], name: str) -> Optional[T]:
    lo, hi = 0, len(catalog) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        current = catalog[mid][0]
        if current == name:
            return catalog[mid][1]
        if current < name:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


def nearest(
    items: Sequence[T],
    distance: Callable[[T], int],
    predicate: Optional[Callable[[T], bool]] = None,
) -> Optional[T]:
    best: Optional[T] = None
    best_d = 1 << 30
    for it in items:
        if predicate is not None and not predicate(it):
            continue
        d = distance(it)
        if d < best_d:
            best_d = d
            best = it
    return best
