from __future__ import annotations

from typing import Callable, List, Optional, Sequence, TypeVar

T = TypeVar("T")


def merge_sort(seq: Sequence[T], key: Callable[[T], object] = lambda x: x) -> List[T]:
    items = list(seq)
    if len(items) <= 1:
        return items
    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    return _merge(left, right, key)


def _merge(left: List[T], right: List[T], key: Callable[[T], object]) -> List[T]:
    result: List[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(right[j]) < key(left[i]):
            result.append(right[j])
            j += 1
        else:
            result.append(left[i])
            i += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def nearest(items: Sequence[T], distance: Callable[[T], int]) -> Optional[T]:
    best: Optional[T] = None
    best_d: Optional[int] = None
    for item in items:
        d = distance(item)
        if best_d is None or d < best_d:
            best, best_d = item, d
    return best
