"""dbzero-backed queue model utilities."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import dbzero as db0


@db0.memo(id="/dbzero/dbzero-modelkit/FQ_Item")
class FQ_Item:  # pylint: disable=invalid-name
    """Single FIFO queue entry storing keyword arguments and its integer key."""

    def __init__(self, key: int, prefix: str | None = None, **kwargs) -> None:
        db0.set_prefix(self, prefix)
        self.__key = key
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def queue_key(self) -> int:
        """Return the index key for this queue item."""
        return self.__key

    def to_dict(self) -> Dict:
        """Return stored item keyword arguments."""
        return {
            key: value
            for key, value in vars(self).items()
            if key != "_FQ_Item__key"
        }


@db0.memo(id="/dbzero/dbzero-modelkit/FiFoQueue")
class FiFoQueue:
    """FIFO queue container backed by a dbzero index."""

    def __init__(self, *, prefix: str | None = None) -> None:
        db0.set_prefix(self, prefix)
        self.__items = db0.index()
        self.__next_key = 0

    def is_empty(self) -> bool:
        """Return True when the queue has no items."""
        return len(self.__items) == 0

    def push_back(self, **kwargs) -> None:
        """Append a single element to the back of the queue."""
        prefix = db0.get_prefix_of(self).name
        self.__items.add(self.__next_key, FQ_Item(self.__next_key, prefix=prefix, **kwargs))
        self.__next_key += 1

    def has_item(
        self,
        filter: Callable,  # pylint: disable=redefined-builtin
        max_scan: int = 100,
    ) -> Optional[bool]:
        """Return whether any queued item matches filter within max_scan items."""
        scanned = 0
        for item in self.__items.select():
            if scanned >= max_scan:
                return None

            scanned += 1
            if filter(**item.to_dict()):
                return True

        return False

    def pop_front(
        self,
        count: int,
        filter: Callable | None = None,  # pylint: disable=redefined-builtin
    ) -> List[Dict]:
        """Retrieve and remove up to count first matching elements from the queue."""
        if filter is not None:
            def _item_filter(item):
                return isinstance(item, FQ_Item) and filter(**item.to_dict())

            query = db0.filter(_item_filter, self.__items.select())
        else:
            query = self.__items.select()

        results = []
        items_to_remove = []

        for item in self.__items.sort(query):
            if len(results) >= count:
                break
            items_to_remove.append(item)
            results.append(item.to_dict())

        for item in items_to_remove:
            self.__items.remove(item.queue_key, item)

        return results
