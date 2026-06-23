from __future__ import annotations

from typing import Generic, Iterator, List, Optional, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    __slots__ = ("value", "next")

    def __init__(self, value: T, nxt: "Optional[Node[T]]" = None) -> None:
        self.value: T = value
        self.next: Optional[Node[T]] = nxt


class LinkedList(Generic[T]):
    def __init__(self) -> None:
        self._head: Optional[Node[T]] = None
        self._tail: Optional[Node[T]] = None
        self._size: int = 0

    def append(self, value: T) -> None:
        node = Node(value)
        if self._tail is None:
            self._head = self._tail = node
        else:
            self._tail.next = node
            self._tail = node
        self._size += 1

    def __iter__(self) -> Iterator[T]:
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return self._size > 0

    def last(self) -> Optional[T]:
        return self._tail.value if self._tail else None

    def to_list(self) -> List[T]:
        return list(self)

    def tail(self, n: int) -> List[T]:
        items = self.to_list()
        return items[-n:] if n > 0 else []
